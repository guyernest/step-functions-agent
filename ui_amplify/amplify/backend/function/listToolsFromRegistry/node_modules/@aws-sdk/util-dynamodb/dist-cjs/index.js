"use strict";
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __name = (target, value) => __defProp(target, "name", { value, configurable: true });
var __export = (target, all) => {
  for (var name in all)
    __defProp(target, name, { get: all[name], enumerable: true });
};
var __copyProps = (to, from, except, desc) => {
  if (from && typeof from === "object" || typeof from === "function") {
    for (let key of __getOwnPropNames(from))
      if (!__hasOwnProp.call(to, key) && key !== except)
        __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
  }
  return to;
};
var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

// src/index.ts
var index_exports = {};
__export(index_exports, {
  NumberValueImpl: () => NumberValue,
  convertToAttr: () => convertToAttr,
  convertToNative: () => convertToNative,
  marshall: () => marshall,
  unmarshall: () => unmarshall
});
module.exports = __toCommonJS(index_exports);

// src/NumberValue.ts
var NumberValue = class _NumberValue {
  static {
    __name(this, "NumberValue");
  }
  value;
  /**
   * This class does not validate that your string input is a valid number.
   *
   * @param value - a precise number, or any BigInt or string, or AttributeValue.
   */
  constructor(value) {
    if (typeof value === "object" && "N" in value) {
      this.value = String(value.N);
    } else {
      this.value = String(value);
    }
    const valueOf = typeof value.valueOf() === "number" ? value.valueOf() : 0;
    const imprecise = valueOf > Number.MAX_SAFE_INTEGER || valueOf < Number.MIN_SAFE_INTEGER || Math.abs(valueOf) === Infinity || Number.isNaN(valueOf);
    if (imprecise) {
      throw new Error(
        `NumberValue should not be initialized with an imprecise number=${valueOf}. Use a string instead.`
      );
    }
  }
  /**
   * This class does not validate that your string input is a valid number.
   *
   * @param value - a precise number, or any BigInt or string, or AttributeValue.
   */
  static from(value) {
    return new _NumberValue(value);
  }
  /**
   * @returns the AttributeValue form for DynamoDB.
   */
  toAttributeValue() {
    return {
      N: this.toString()
    };
  }
  /**
   * @returns BigInt representation.
   *
   * @throws SyntaxError if the string representation is not convertable to a BigInt.
   */
  toBigInt() {
    const stringValue = this.toString();
    return BigInt(stringValue);
  }
  /**
   * @override
   *
   * @returns string representation. This is the canonical format in DynamoDB.
   */
  toString() {
    return String(this.value);
  }
  /**
   * @override
   */
  valueOf() {
    return this.toString();
  }
};

// src/convertToAttr.ts
var convertToAttr = /* @__PURE__ */ __name((data, options) => {
  if (data === void 0) {
    throw new Error(`Pass options.removeUndefinedValues=true to remove undefined values from map/array/set.`);
  } else if (data === null && typeof data === "object") {
    return convertToNullAttr();
  } else if (Array.isArray(data)) {
    return convertToListAttr(data, options);
  } else if (data?.constructor?.name === "Set") {
    return convertToSetAttr(data, options);
  } else if (data?.constructor?.name === "Map") {
    return convertToMapAttrFromIterable(data, options);
  } else if (data?.constructor?.name === "Object" || // for object which is result of Object.create(null), which doesn't have constructor defined
  !data.constructor && typeof data === "object") {
    return convertToMapAttrFromEnumerableProps(data, options);
  } else if (isBinary(data)) {
    if (data.length === 0 && options?.convertEmptyValues) {
      return convertToNullAttr();
    }
    return convertToBinaryAttr(data);
  } else if (typeof data === "boolean" || data?.constructor?.name === "Boolean") {
    return { BOOL: data.valueOf() };
  } else if (typeof data === "number" || data?.constructor?.name === "Number") {
    return convertToNumberAttr(data, options);
  } else if (data instanceof NumberValue) {
    return data.toAttributeValue();
  } else if (typeof data === "bigint") {
    return convertToBigIntAttr(data);
  } else if (typeof data === "string" || data?.constructor?.name === "String") {
    if (data.length === 0 && options?.convertEmptyValues) {
      return convertToNullAttr();
    }
    return convertToStringAttr(data);
  } else if (options?.convertClassInstanceToMap && typeof data === "object") {
    return convertToMapAttrFromEnumerableProps(data, options);
  }
  throw new Error(
    `Unsupported type passed: ${data}. Pass options.convertClassInstanceToMap=true to marshall typeof object as map attribute.`
  );
}, "convertToAttr");
var convertToListAttr = /* @__PURE__ */ __name((data, options) => ({
  L: data.filter(
    (item) => typeof item !== "function" && (!options?.removeUndefinedValues || options?.removeUndefinedValues && item !== void 0)
  ).map((item) => convertToAttr(item, options))
}), "convertToListAttr");
var convertToSetAttr = /* @__PURE__ */ __name((set, options) => {
  const setToOperate = options?.removeUndefinedValues ? new Set([...set].filter((value) => value !== void 0)) : set;
  if (!options?.removeUndefinedValues && setToOperate.has(void 0)) {
    throw new Error(`Pass options.removeUndefinedValues=true to remove undefined values from map/array/set.`);
  }
  if (setToOperate.size === 0) {
    if (options?.convertEmptyValues) {
      return convertToNullAttr();
    }
    throw new Error(`Pass a non-empty set, or options.convertEmptyValues=true.`);
  }
  const item = setToOperate.values().next().value;
  if (item instanceof NumberValue) {
    return {
      NS: Array.from(setToOperate).map((_) => _.toString())
    };
  } else if (typeof item === "number") {
    return {
      NS: Array.from(setToOperate).map((num) => convertToNumberAttr(num, options)).map((item2) => item2.N)
    };
  } else if (typeof item === "bigint") {
    return {
      NS: Array.from(setToOperate).map(convertToBigIntAttr).map((item2) => item2.N)
    };
  } else if (typeof item === "string") {
    return {
      SS: Array.from(setToOperate).map(convertToStringAttr).map((item2) => item2.S)
    };
  } else if (isBinary(item)) {
    return {
      // Do not alter binary data passed https://github.com/aws/aws-sdk-js-v3/issues/1530
      // @ts-expect-error Type 'ArrayBuffer' is not assignable to type 'Uint8Array'
      BS: Array.from(setToOperate).map(convertToBinaryAttr).map((item2) => item2.B)
    };
  } else {
    throw new Error(`Only Number Set (NS), Binary Set (BS) or String Set (SS) are allowed.`);
  }
}, "convertToSetAttr");
var convertToMapAttrFromIterable = /* @__PURE__ */ __name((data, options) => ({
  M: ((data2) => {
    const map = {};
    for (const [key, value] of data2) {
      if (typeof value !== "function" && (value !== void 0 || !options?.removeUndefinedValues)) {
        map[key] = convertToAttr(value, options);
      }
    }
    return map;
  })(data)
}), "convertToMapAttrFromIterable");
var convertToMapAttrFromEnumerableProps = /* @__PURE__ */ __name((data, options) => ({
  M: ((data2) => {
    const map = {};
    for (const key in data2) {
      const value = data2[key];
      if (typeof value !== "function" && (value !== void 0 || !options?.removeUndefinedValues)) {
        map[key] = convertToAttr(value, options);
      }
    }
    return map;
  })(data)
}), "convertToMapAttrFromEnumerableProps");
var convertToNullAttr = /* @__PURE__ */ __name(() => ({ NULL: true }), "convertToNullAttr");
var convertToBinaryAttr = /* @__PURE__ */ __name((data) => ({ B: data }), "convertToBinaryAttr");
var convertToStringAttr = /* @__PURE__ */ __name((data) => ({ S: data.toString() }), "convertToStringAttr");
var convertToBigIntAttr = /* @__PURE__ */ __name((data) => ({ N: data.toString() }), "convertToBigIntAttr");
var validateBigIntAndThrow = /* @__PURE__ */ __name((errorPrefix) => {
  throw new Error(`${errorPrefix} Use NumberValue from @aws-sdk/lib-dynamodb.`);
}, "validateBigIntAndThrow");
var convertToNumberAttr = /* @__PURE__ */ __name((num, options) => {
  if ([Number.NaN, Number.POSITIVE_INFINITY, Number.NEGATIVE_INFINITY].map((val) => val.toString()).includes(num.toString())) {
    throw new Error(`Special numeric value ${num.toString()} is not allowed`);
  } else if (!options?.allowImpreciseNumbers) {
    if (Number(num) > Number.MAX_SAFE_INTEGER) {
      validateBigIntAndThrow(`Number ${num.toString()} is greater than Number.MAX_SAFE_INTEGER.`);
    } else if (Number(num) < Number.MIN_SAFE_INTEGER) {
      validateBigIntAndThrow(`Number ${num.toString()} is lesser than Number.MIN_SAFE_INTEGER.`);
    }
  }
  return { N: num.toString() };
}, "convertToNumberAttr");
var isBinary = /* @__PURE__ */ __name((data) => {
  const binaryTypes = [
    "ArrayBuffer",
    "Blob",
    "Buffer",
    "DataView",
    "File",
    "Int8Array",
    "Uint8Array",
    "Uint8ClampedArray",
    "Int16Array",
    "Uint16Array",
    "Int32Array",
    "Uint32Array",
    "Float32Array",
    "Float64Array",
    "BigInt64Array",
    "BigUint64Array"
  ];
  if (data?.constructor) {
    return binaryTypes.includes(data.constructor.name);
  }
  return false;
}, "isBinary");

// src/convertToNative.ts
var convertToNative = /* @__PURE__ */ __name((data, options) => {
  for (const [key, value] of Object.entries(data)) {
    if (value !== void 0) {
      switch (key) {
        case "NULL":
          return null;
        case "BOOL":
          return Boolean(value);
        case "N":
          return convertNumber(value, options);
        case "B":
          return convertBinary(value);
        case "S":
          return convertString(value);
        case "L":
          return convertList(value, options);
        case "M":
          return convertMap(value, options);
        case "NS":
          return new Set(value.map((item) => convertNumber(item, options)));
        case "BS":
          return new Set(value.map(convertBinary));
        case "SS":
          return new Set(value.map(convertString));
        default:
          throw new Error(`Unsupported type passed: ${key}`);
      }
    }
  }
  throw new Error(`No value defined: ${JSON.stringify(data)}`);
}, "convertToNative");
var convertNumber = /* @__PURE__ */ __name((numString, options) => {
  if (typeof options?.wrapNumbers === "function") {
    return options?.wrapNumbers(numString);
  }
  if (options?.wrapNumbers) {
    return NumberValue.from(numString);
  }
  const num = Number(numString);
  const infinityValues = [Number.POSITIVE_INFINITY, Number.NEGATIVE_INFINITY];
  const isLargeFiniteNumber = (num > Number.MAX_SAFE_INTEGER || num < Number.MIN_SAFE_INTEGER) && !infinityValues.includes(num);
  if (isLargeFiniteNumber) {
    if (typeof BigInt === "function") {
      try {
        return BigInt(numString);
      } catch (error) {
        throw new Error(`${numString} can't be converted to BigInt. Set options.wrapNumbers to get string value.`);
      }
    } else {
      throw new Error(`${numString} is outside SAFE_INTEGER bounds. Set options.wrapNumbers to get string value.`);
    }
  }
  return num;
}, "convertNumber");
var convertString = /* @__PURE__ */ __name((stringValue) => stringValue, "convertString");
var convertBinary = /* @__PURE__ */ __name((binaryValue) => binaryValue, "convertBinary");
var convertList = /* @__PURE__ */ __name((list, options) => list.map((item) => convertToNative(item, options)), "convertList");
var convertMap = /* @__PURE__ */ __name((map, options) => Object.entries(map).reduce(
  (acc, [key, value]) => (acc[key] = convertToNative(value, options), acc),
  {}
), "convertMap");

// src/marshall.ts
function marshall(data, options) {
  const attributeValue = convertToAttr(data, options);
  const [key, value] = Object.entries(attributeValue)[0];
  switch (key) {
    case "M":
    case "L":
      return options?.convertTopLevelContainer ? attributeValue : value;
    case "SS":
    case "NS":
    case "BS":
    case "S":
    case "N":
    case "B":
    case "NULL":
    case "BOOL":
    case "$unknown":
    default:
      return attributeValue;
  }
}
__name(marshall, "marshall");

// src/unmarshall.ts
var unmarshall = /* @__PURE__ */ __name((data, options) => {
  if (options?.convertWithoutMapWrapper) {
    return convertToNative(data, options);
  }
  return convertToNative({ M: data }, options);
}, "unmarshall");
// Annotate the CommonJS export names for ESM import in node:

0 && (module.exports = {
  NumberValueImpl,
  convertToAttr,
  convertToNative,
  marshall,
  unmarshall
});

