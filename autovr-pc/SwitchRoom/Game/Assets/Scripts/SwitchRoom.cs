using UnityEngine;
using UnityEngine.UI;
using UnityEngine.EventSystems;

public sealed class SwitchRoom : MonoBehaviour
{
    public Button open, close, collect;
    public GameObject vault;
    public Text scoreLabel;
    int score;

    void Awake()
    {
        if (System.Array.IndexOf(System.Environment.GetCommandLineArgs(), "-switchRoomVerify") < 0)
            return;
        var eventSystem = Object.FindFirstObjectByType<EventSystem>();
        if (!eventSystem)
            throw new System.InvalidOperationException("SwitchRoom verification requires the scene EventSystem.");
        eventSystem.enabled = false;
        Debug.Log("SWITCHROOM_TEST_INPUT_DISABLED");
    }

    void Start()
    {
        open.onClick.AddListener(OpenVault);
        close.onClick.AddListener(CloseVault);
        collect.onClick.AddListener(Collect);
        Record("ready");
    }

    public void SharedLog() { Record("shared"); }
    void OpenVault() { vault.SetActive(true); Record("open"); }
    void CloseVault() { vault.SetActive(false); Record("close"); }
    void Collect()
    {
        if (!vault.activeSelf) return;
        score++;
        scoreLabel.text = "CORES RECOVERED   " + score;
        vault.SetActive(false);
        Record("collect");
    }
    void Record(string action)
    {
        Debug.Log("SWITCHROOM|" + action + "|" + (vault.activeSelf ? "open" : "closed") + "|" + score);
    }
}
