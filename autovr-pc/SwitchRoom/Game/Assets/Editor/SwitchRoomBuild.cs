using System.IO;
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.Build.Reporting;
using UnityEditor.Events;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

public static class SwitchRoomBuild
{
    const string Scene = "Assets/SwitchRoom.unity";
    static readonly Color Light = new Color(.91f, .96f, .96f);
    static RectTransform Rect(string name, Transform parent, Vector2 position, Vector2 size)
    {
        var rect = new GameObject(name, typeof(RectTransform)).GetComponent<RectTransform>();
        rect.SetParent(parent, false);
        rect.sizeDelta = size;
        rect.anchoredPosition = position;
        return rect;
    }

    static Text Label(string name, string text, Transform parent, int y, int size)
    {
        var label = Rect(name, parent, new Vector2(0,y), new Vector2(740,60)).gameObject.AddComponent<Text>();
        label.font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
        label.fontSize = size;
        label.alignment = TextAnchor.MiddleCenter;
        label.color = Light;
        label.text = text;
        label.raycastTarget = false;
        return label;
    }

    static Button Key(string name, string caption, Transform parent, int x, int y, Color color)
    {
        var rect = Rect(name, parent, new Vector2(x,y), new Vector2(210,56));
        var image = rect.gameObject.AddComponent<Image>();
        image.color = color;
        var button = rect.gameObject.AddComponent<Button>();
        button.targetGraphic = image;
        Label("Caption", caption, rect, 0, 22);
        return button;
    }

    [MenuItem("Switch Room/Create or rebuild demo scene")]
    public static void CreateScene()
    {
        var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        var cam = new GameObject("Camera").AddComponent<Camera>();
        cam.clearFlags = CameraClearFlags.SolidColor;
        cam.backgroundColor = new Color(.04f,.08f,.13f);
        new GameObject("EventSystem", typeof(EventSystem), typeof(StandaloneInputModule));
        var canvas = new GameObject("Canvas", typeof(RectTransform), typeof(Canvas), typeof(CanvasScaler),
                                    typeof(GraphicRaycaster));
        canvas.GetComponent<Canvas>().renderMode = RenderMode.ScreenSpaceOverlay;
        var scaler = canvas.GetComponent<CanvasScaler>();
        scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
        scaler.referenceResolution = new Vector2(900,560);
        scaler.matchWidthOrHeight = .5f;
        var t = canvas.transform;
        var game = new GameObject("Switch Room").AddComponent<SwitchRoom>();
        Label("Title", "SWITCH ROOM", t, 190, 46);
        Label("Instructions", "Open the vault and recover an energy core.", t, 133, 22);
        game.scoreLabel = Label("Score", "CORES RECOVERED   0", t, 76, 22);
        game.open = Key("ButtonA", "A   /   OPEN", t, -125, 0, new Color(.07f,.42f,.41f));
        game.close = Key("ButtonB", "B   /   CLOSE", t, 125, 0, new Color(.44f,.22f,.26f));
        game.vault = Rect("ResultPanel", t, new Vector2(0,-144), new Vector2(510,160)).gameObject;
        game.vault.AddComponent<Image>().color = new Color(.48f,.13f,.19f);
        Label("VaultState", "VAULT OPEN", game.vault.transform, 40, 22);
        game.collect = Key("CollectCore", "RECOVER CORE", game.vault.transform, 0, -22, new Color(.21f,.26f,.39f));
        UnityEventTools.AddPersistentListener(game.open.onClick, game.SharedLog);
        UnityEventTools.AddPersistentListener(game.close.onClick, game.SharedLog);
        game.vault.SetActive(false);
        if (!EditorSceneManager.SaveScene(scene, Scene)) throw new BuildFailedException("Scene save failed");
        EditorBuildSettings.scenes = new[] { new EditorBuildSettingsScene(Scene, true) };
    }

    [MenuItem("Switch Room/Build Windows IL2CPP game")]
    public static void Build()
    {
        CreateScene();
        PlayerSettings.SetScriptingBackend(NamedBuildTarget.Standalone, ScriptingImplementation.IL2CPP);
        PlayerSettings.productName = "SwitchRoom";
        PlayerSettings.runInBackground = true;
        PlayerSettings.fullScreenMode = FullScreenMode.Windowed;
        PlayerSettings.defaultScreenWidth = 900;
        PlayerSettings.defaultScreenHeight = 560;
        var dir = Path.GetFullPath(Path.Combine(Application.dataPath, "../../Build"));
        Directory.CreateDirectory(dir);
        var report = BuildPipeline.BuildPlayer(new BuildPlayerOptions {
            scenes = new[] { Scene }, locationPathName = Path.Combine(dir,"SwitchRoom.exe"),
            target = BuildTarget.StandaloneWindows64, options = BuildOptions.Development
        });
        if (report.summary.result != BuildResult.Succeeded)
            throw new BuildFailedException("Build result: " + report.summary.result);
    }
}
