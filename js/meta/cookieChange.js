/**
 * Relevant documentation:
 *  - Object.getOwnPropertyDescriptor(): https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/getOwnPropertyDescriptor
 *  - Object.defineProperty(): https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/defineProperty
 *  - Patching cookie property example: https://stackoverflow.com/a/63952971/15493645
 *  - Reflect: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Reflect
 *  - Object.defineProperty() vs obj.key=value: https://stackoverflow.com/a/26920526/15493645
 */

/**
 *  Patch document's cookie property to report with an event upon change.
 */
(function () {
  "use strict";
  var _cookieEventEnum = {
    CookieChange: "CookieChange",
  };
  // Cookies are a semicolon separated list of key=value pairs
  /** @type {string} */
  var _lastCookie = document.cookie;
  // listen cookie-change messages from other same-origin tabs/frames
  var _cookieChannel = new BroadcastChannel("cookie-change");
  _cookieChannel.addEventListener("onmessage", function (event) {
    _lastCookie = event.data.newCookie;
    document.dispatchEvent(
      new CustomEvent(_cookieEventEnum.CookieChange, {
        detail: event.data,
      }),
    );
  });
  /**
   * Getting property configuration
   * @type {PropertyDescriptor | undefined}
   */
  const nativeObjBuffer = Object.getOwnPropertyDescriptor(
    Document.prototype,
    "cookie",
  );
  // cloning property configuration
  Object.defineProperty(
    Document.prototype,
    "_nativeCookieObj",
    nativeObjBuffer,
  );
  // Defining new "cookie" property that intercepts changes
  Object.defineProperty(Document.prototype, "cookie", {
    enumerable: true,
    configurable: true,
    get() {
      return _nativeCookieObj;
    },
    /** @param {string} cookie */
    set(cookie) {
      _nativeCookieObj = cookie;
      if (cookie === _lastCookie) return;
      const eventState = {
        /** @type {CookieChangeDetail} */
        detail: { oldCookie: _lastCookie, newCookie: cookie },
      };
      try {
        this.dispatchEvent(
          new CustomEvent(_cookieEventEnum.CookieChange, eventState),
        );
        _cookieChannel.postMessage(eventState.detail);
      } finally {
        _lastCookie = cookie;
      }
    },
  });
  // addEventListener
  window.addEventListener(_cookieEventEnum.CookieChange, _cookieChangeHandler, {
    capture: true,
  });
})();
