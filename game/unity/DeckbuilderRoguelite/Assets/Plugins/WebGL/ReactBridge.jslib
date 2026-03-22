mergeInto(LibraryManager.library, {
  SendCombatStateToReact: function (jsonPtr) {
    var json = UTF8ToString(jsonPtr);
    // Dispatches to react-unity-webgl event listeners
    if (typeof window.dispatchReactUnityEvent === "function") {
      window.dispatchReactUnityEvent("OnCombatStateChanged", json);
    }
  },

  SendGameEventToReact: function (eventNamePtr, jsonPtr) {
    var eventName = UTF8ToString(eventNamePtr);
    var json = UTF8ToString(jsonPtr);
    if (typeof window.dispatchReactUnityEvent === "function") {
      window.dispatchReactUnityEvent(eventName, json);
    }
  },
});
