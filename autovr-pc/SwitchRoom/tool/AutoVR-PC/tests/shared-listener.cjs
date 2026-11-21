// Execute the PC agent against two independent fake UnityEvents sharing a callback.
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const assert = require("node:assert/strict");
const bundle = fs.readFileSync(path.join(__dirname, "../ts/pc-agent.js"));
const length = Number(bundle.toString("utf8", 0, 128).match(/(\d+) \/pc\.js/)[1]);
const marker = Buffer.from("✄\n");
const start = bundle.indexOf(marker) + marker.length;
const code = bundle.subarray(start, start + length).toString("utf8")
                   .replace('import "frida-il2cpp-bridge";', "");
const method = fn => ({invoke: fn});
const base = {isAssignableFrom: () => true};
const component = {handle: {equals: other => other === component.handle}, type: {object: {}}};
const field = {name: "m_OnClick", type: {class: {}}, offset: 16};
const button = {name: "Button", parent: component, fields: [field],
                handle: {toString: () => "button", equals: () => false}};
let calls = [];
function SharedLog() { calls.push("shared"); }
function fakeButton(id) {
    const event = {
        method: name => method(() => name === "GetPersistentEventCount" ? 1 : {content: "SharedLog"}),
        tryField: () => undefined,
        tryMethod: () => method(() => { SharedLog(); calls.push(id); })
    };
    return {class: button, isNull: () => false,
        handle: {add: () => ({readPointer: () => ({isNull: () => false, event})})},
        method: name => method(() => name === "GetInstanceID" ? id : {content: "Button " + id}),
        tryMethod: () => method(() => true)};
}
const buttons = [fakeButton(21), fakeButton(22)];
let sceneHandle = 3;
const scene = {method: name => method(() => name === "get_name" ? {content: "Main"} : sceneHandle)};
const classes = {"UnityEngine.Events.UnityEventBase": base, "UnityEngine.Component": component,
    "UnityEngine.Object": {method: () => ({overload: () => method(() => buttons)})},
    "UnityEngine.SceneManagement.SceneManager": {method: () => method(() => ({box: () => scene}))}};
const rpc = {};
vm.runInNewContext(code, {rpc, Il2Cpp: {perform: f => f(), Object: function(ptr) {return ptr.event;},
    domain: {assembly: () => ({image: {class: name => classes[name]}})}}});
assert.equal(rpc.exports.scan().value.sceneHandle, 3);
for (let attempt = 0; attempt < 2; attempt++) {
    sceneHandle = {type: {class: {valueTypeSize: 4}}, handle: {
        readByteArray: n => Uint8Array.from([42, 0, 0, 0].slice(0, n)).buffer
    }};
    assert.equal(rpc.exports.scan().value.sceneHandle, "2a000000");
}
const rows = rpc.exports.scan().value.events;
assert.deepEqual(Array.from(rows, r => r.id), ["21/16", "22/16"]);
assert.equal(rpc.exports.trigger("21/16").value.status, "Invoke returned");
assert.deepEqual(calls, ["shared", 21]);
buttons.shift();
assert.equal(rpc.exports.trigger("21/16").ok, false);
assert.deepEqual(calls, ["shared", 21]);
console.log("PASS shared listener selection and disappeared event");
