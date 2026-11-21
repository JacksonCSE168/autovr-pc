// Windows port of the component and listener discovery in AutoVR's events.ts.
import "frida-il2cpp-bridge";

type Obj = Il2Cpp.Object;
type Candidate = {id: string, object: string, component: string, field: string,
                  persistent: string[], runtimeEntries: number | null, callable: boolean};

function mainThread<T>(work: () => T) {
    // Capture managed exceptions inside the scheduled callback so RPC completes.
    return Il2Cpp.perform(() => {
        try { return {ok: true, value: work()}; }
        catch (error) { return {ok: false, error: String(error)}; }
    }, "main");
}

function core() { return Il2Cpp.domain.assembly("UnityEngine.CoreModule").image; }
function sceneManager() { return core().class("UnityEngine.SceneManagement.SceneManager"); }

function listeners(event: Obj) {
    const persistent: string[] = [];
    const count = event.method<number>("GetPersistentEventCount", 0).invoke();
    for (let i = 0; i < count; i++) {
        persistent.push(event.method<Il2Cpp.String>("GetPersistentMethodName", 1).invoke(i).content ?? "");
    }
    // Same InvokableCallList path as EventLoader.getCallsFromICL in AutoVR.
    const calls = event.tryField<Obj>("m_Calls")?.value;
    const runtime = calls && !calls.isNull() ? calls.tryField<Obj>("m_RuntimeCalls")?.value : undefined;
    const runtimeEntries = runtime && !runtime.isNull() ? runtime.tryMethod<number>("get_Count", 0)?.invoke() ?? null : null;
    return {persistent, runtimeEntries};
}

// Unity can expose the scene handle as an integer or a small value type.
// Serialize the value itself: a boxed return may live at a new address on each scan.
function sceneHandleKey(scene: Obj): number | string {
    const value = scene.method<number | Il2Cpp.ValueType>("get_handle", 0).invoke();
    if (typeof value === "number") return value;
    const bytes = value.handle.readByteArray(value.type.class.valueTypeSize);
    if (!bytes) throw new Error("Unable to read the scene handle value");
    return Array.from(new Uint8Array(bytes), b => b.toString(16).padStart(2, "0")).join("");
}

function enumerate(selected?: string) {
    const image = core();
    const base = image.class("UnityEngine.Events.UnityEventBase");
    const component = image.class("UnityEngine.Component");
    const find = image.class("UnityEngine.Object").method<Il2Cpp.Array<Obj>>("FindObjectsOfType")
                      .overload("System.Type");
    const events: Candidate[] = [];
    const warnings = new Set<string>();
    const fieldsByClass = new Map<string, Il2Cpp.Field[]>();
    for (const comp of find.invoke(component.type.object)) {
        if (comp.isNull()) continue;
        const klass = comp.class;
        let fields = fieldsByClass.get(klass.handle.toString());
        if (!fields) {
            fields = [];
            for (let k: Il2Cpp.Class | null = klass; k && !k.handle.equals(component.handle); k = k.parent) {
                for (const field of k.fields) {
                    if (!field.isStatic && base.isAssignableFrom(field.type.class)) fields.push(field);
                }
            }
            fieldsByClass.set(klass.handle.toString(), fields);
        }
        if (!fields.length) continue;
        if (comp.tryMethod<boolean>("get_isActiveAndEnabled", 0)?.invoke() === false) continue;
        for (const f of fields) {
            const id = comp.method<number>("GetInstanceID", 0).invoke() + "/" + f.offset;
            if (selected !== undefined && selected !== id) continue;
            try {
                // Read the declared field by offset so hidden base fields remain distinct.
                const address = comp.handle.add(f.offset).readPointer();
                if (address.isNull()) continue;
                const event = new Il2Cpp.Object(address);
                const invoke = event.tryMethod("Invoke", 0);
                const interactable = comp.tryMethod<boolean>("IsInteractable", 0);
                const callable = !!invoke && (!interactable || interactable.invoke());
                if (selected !== undefined) {
                    if (!callable) throw new Error("Event is disabled or requires arguments");
                    invoke!.invoke();
                    return {id, status: "Invoke returned"};
                }
                events.push({id, object: comp.method<Il2Cpp.String>("get_name", 0).invoke().content ?? "",
                    component: klass.name, field: f.name, callable, ...listeners(event)});
            } catch (e) {
                if (selected !== undefined) throw e;
                warnings.add(klass.name + "." + f.name + ": " + String(e));
            }
        }
    }
    if (selected !== undefined) throw new Error("Event is no longer active: " + selected);
    const scene = sceneManager().method<Il2Cpp.ValueType>("GetActiveScene", 0).invoke().box();
    return {scene: scene.method<Il2Cpp.String>("get_name", 0).invoke().content,
            sceneHandle: sceneHandleKey(scene),
            events, warnings: Array.from(warnings)};
}

rpc.exports = {
    ready() { return Process.platform === "windows" && Process.findModuleByName("GameAssembly.dll") !== null; },
    scan() { return mainThread(() => enumerate()); },
    trigger(id: string) { return mainThread(() => enumerate(id)); },
    loadScene(index: number) {
        return mainThread(() => {
            const manager = sceneManager();
            const count = manager.method<number>("get_sceneCountInBuildSettings", 0).invoke();
            if (!Number.isInteger(index) || index < 0 || index >= count) throw new Error("Scene index outside build settings");
            manager.method("LoadScene").overload("System.Int32").invoke(index);
            return index;
        });
    },
    activeIndex() { return mainThread(() => sceneManager().method<Il2Cpp.ValueType>("GetActiveScene", 0).invoke().box()
                                      .method<number>("get_buildIndex", 0).invoke()); }
};
