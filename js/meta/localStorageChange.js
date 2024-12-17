/**
 * Relevant documentation:
 *  - Proxy/handler: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Proxy/Proxy
 *  - handler.get(): https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Proxy/Proxy/get
 *  - handler.set(): https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Proxy/Proxy/set
 *  - Object.getOwnPropertyDescriptor(): https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/getOwnPropertyDescriptor
 *  - Object.defineProperty(): https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/defineProperty
 *  - "storage" event: https://developer.mozilla.org/en-US/docs/Web/API/Window/storage_event
 *  - StorageEvent object: https://developer.mozilla.org/en-US/docs/Web/API/StorageEvent
 *  - Storage object: https://developer.mozilla.org/en-US/docs/Web/API/Storage
 *  - Proxy usage example (metaprogramming): https://stackoverflow.com/a/7891968/15493645
 *  - Patching cookie property example: https://stackoverflow.com/a/63952971/15493645
 *  - Reflect: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Reflect
 *  - Object.defineProperty() vs obj.key=value: https://stackoverflow.com/a/26920526/15493645
 */

/**
 * Local storage data state object
 * @typedef {Object} LocalStorageState
 * @property {number} length
 * @property {string[]} keys
 * @property {object} storageContent
 */

/**
 * Local storage event detail object
 * @typedef {Object} LocalStorageEventDetail
 * @property {string} oldLocalStorage stringfied LocalStorageStage
 * @property {string} newLocalStorage stringfied LocalStorageStage
 */

/**
 * Local storage property overwritten event detail object
 * @typedef {Object} LocalStorageOvewrittenEventDetail
 * @property {number} timeWhen unix millis (float)
 * @property {string} localStorageBefore stringfied LocalStorageStage
 */

/**
 *  Watch changes in localStorage object and report with an event
 */
(function () {
  "use strict";
  var _localStorageEventEnum = {
    LocalStorageChange: "LocalStorageChange",
    LocalStoragePropertyOverwritten: "LocalStoragePropertyOverwritten",
  };
  /**
   * @return {string}  stringfied LocalStorageStage
   */
  var _getLocalStorageDetail = function () {
    /** @type {LocalStorageState} */
    const detail = {
      length: localStorage.length,
      keys: [],
      storageContent: {},
    };
    for (let i = 0; i < localStorage.length; ++i) {
      const key = localStorage.key(i);
      if (Object.is(key, null) || key === "") continue;
      detail.keys.push(key);
      detail.storageContent[key] = localStorage.getItem(key) || "";
    }
    return JSON.stringify(detail);
  };
  /** @type {string} */
  var _lastLocalStorage = _getLocalStorageDetail();
  /**
   * Getting propery configuration
   * @type {PropertyDescriptor}
   */
  const nativeLocalStorageObj = Object.getOwnPropertyDescriptor(
    Window.prototype,
    "localStorage",
  );
  // Cloning property configuration
  Object.defineProperty(
    Window.prototype,
    "_nativeLocalStorageObj",
    nativeLocalStorageObj,
  );
  /**
   * Listen cookie-change messages from other same-origin tabs/frames
   * NOTE: No broadcast channel for PropertyOverwritten event because that should be
   * a per-window matter.
   * NOTE: PropertyOverwritte event was probably a bad idea, but it's done already, so
   * let's see what it's worth...
   */
  var _localStorageChannel = new BroadcastChannel("localstorage-change");
  _localStorageChannel.addEventListener("onmessage", function (event) {
    _lastLocalStorage = event.data.newLocalStorage;
    document.dispatchEvent(
      new CustomEvent(_localStorageEventEnum.LocalStorageChange, {
        detail: event.data,
      }),
    );
  });
  // Proxy object that watches property assignments
  var _proxyLocalStorage = new Proxy(_nativeLocalStorageObj, {
    /**
     * Method called when accessing properties. Patches .setItem()
     * The `this` keyword is bound the handler object where this method is **defined**.
     * @param {Storage} target localStorage instance
     * @param {string|Symbol} property name to be assigned to
     * @param {Proxy} receiver proxy object calling handler trap
     */
    get(target, property, receiver) {
      if (property === "setItem") {
        return function (key, value) {
          // calls this.set()
          Reflect.set(receiver, key, value, receiver);
        };
      }
      return Reflect.get(target, property, receiver);
    },
    /**
     * Method called when properties are being set with `Object.property = value`.
     * The `this` keyword is bound the handler object where this method is **defined**.
     * The proxy object in question, or a subclass of it, are available as the
     * `receiver` parameter.
     * @param {Storage} target localStorage instance
     * @param {string|Symbol} property name to be assigned to
     * @param {any} value value that will be assigned to property
     * @param {Proxy} receiver proxy object calling handler trap
     * @return {boolean} status code of call: true for success and false for error
     */
    set(target, property, value, receiver) {
      Reflect.apply(target.setItem, target, [property, value]);
      const currentLocalStorage = _getLocalStorageDetail();
      if (_lastLocalStorage === currentLocalStorage) return;
      const eventState = {
        /** @type {LocalStorageEventDetail} */
        detail: {
          oldLocalStorage: _lastLocalStorage,
          newLocalStorage: currentLocalStorage,
        },
      };
      try {
        window.dispatchEvent(
          new CustomEvent(
            _localStorageEventEnum.LocalStorageChange,
            eventState,
          ),
        );
        _localStorageChannel.postMesage(eventState.detail);
      } finally {
        _lastLocalStorage = currentLocalStorage;
      }
    },
  });
  // Redirecting localStorage to buffer property
  Object.defineProperty(Window.prototype, "localStorage", {
    enumerable: true,
    configurable: true,
    get() {
      return _proxyLocalStorage;
    },
    /** @param {any} value */
    set(value) {
      _nativeLocalStorageObj = value;
      const eventState = {
        /** @type {LocalStorageOvewrittenEventDetail} */
        detail: {
          timeWhen: Date.now(),
          localStorageBefore: _lastLocalStorage,
        },
      };
      window.dispatchEvent(
        new CustomEvent(
          _localStorageEventEnum.LocalStoragePropertyOverwritten,
          eventState,
        ),
      );
      console.error("ROBO-ESOCIAL: Local storage object has been overwritten");
    },
  });
})();
