import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { getSerdePlugin } from "@smithy/middleware-serde";
import { Command as $Command } from "@smithy/smithy-client";
import { commonParams } from "../endpoint/EndpointParameters";
import { de_CreateActivityCommand, se_CreateActivityCommand } from "../protocols/Aws_json1_0";
export { $Command };
export class CreateActivityCommand extends $Command
    .classBuilder()
    .ep(commonParams)
    .m(function (Command, cs, config, o) {
    return [
        getSerdePlugin(config, this.serialize, this.deserialize),
        getEndpointPlugin(config, Command.getEndpointParameterInstructions()),
    ];
})
    .s("AWSStepFunctions", "CreateActivity", {})
    .n("SFNClient", "CreateActivityCommand")
    .f(void 0, void 0)
    .ser(se_CreateActivityCommand)
    .de(de_CreateActivityCommand)
    .build() {
}
