declare var _nativeCookieObj: string;

type CookieEventEnum = {
  CookieChange: string,
};

declare var _cookieEventEnum: CookieEventEnum;

type CookieChangeDetail = {
  oldCookie: string,
  newCookie: string,
}

declare function _cookieChangeHandler(detail: CookieChangeDetail): void {}
