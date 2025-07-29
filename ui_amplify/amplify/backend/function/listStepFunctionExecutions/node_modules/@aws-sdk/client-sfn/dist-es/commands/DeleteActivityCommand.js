import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { getSerdePlugin } from "@smithy/middleware-serde";
import { Command as $Command } from "@smithy/smithy-client";
import { commonParams } from "../endpoint/EndpointParameters";
import { de_DeleteActivityCommand, se_DeleteActivityCommand } from "../protocols/Aws_json1_0";
export { $Command };
export class DeleteActivityCommand extends $Command
    .classBuilder()
    .ep(commonParams)
    .m(function (Command, cs, config, o) {
    return [
        getSerdePlugin(config, this.serialize, this.deserialize),
        getEndpointPlugin(config, Command.getEndpointParameterInstructions()),
    ];
})
    .s("AWSStepFunctions", "DeleteActivity", {})
    .n("SFNClient", "DeleteActivityCommand")
    .f(void 0, void 0)
    .ser(se_DeleteActivityCommand)
    .de(de_DeleteActivityCommand)
    .build() {
}
