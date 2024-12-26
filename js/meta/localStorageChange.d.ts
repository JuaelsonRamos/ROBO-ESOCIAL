declare var _nativeLocalStorageObj: Storage;

type LocalStorageEventEnum = {
  LocalStorageChange: string,
  LocalStoragePropertyOverwritten: string,
}

declare var _localStorageEventEnum: LocalStorageEventEnum;

type LocalStorageState = {
  length: number,
  keys: string[],
  storageContent: object,
}

type LocalStorageEventDetail = {
  /** stringfied LocalStorageState */
  oldLocalStorage: string,
  /** stringfied LocalStorageState */
  newLocalStorage: string,
}

type LocalStorageOvewrittenEventDetail = {
  /** unix millis (float) */
  timeWhen: number,
  /** stringfied LocalStorageState */
  localStoragebefore: string,
}

declare function _localStorageChangeHandler(detail: LocalStorageEventDetail): void {}
