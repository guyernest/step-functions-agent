import { ServiceException as __ServiceException, } from "@smithy/smithy-client";
export { __ServiceException };
export class SFNServiceException extends __ServiceException {
    constructor(options) {
        super(options);
        Object.setPrototypeOf(this, SFNServiceException.prototype);
    }
}
