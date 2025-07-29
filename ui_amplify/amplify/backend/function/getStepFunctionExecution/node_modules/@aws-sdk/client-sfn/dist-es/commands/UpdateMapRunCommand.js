import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { getSerdePlugin } from "@smithy/middleware-serde";
import { Command as $Command } from "@smithy/smithy-client";
import { commonParams } from "../endpoint/EndpointParameters";
import { de_UpdateMapRunCommand, se_UpdateMapRunCommand } from "../protocols/Aws_json1_0";
export { $Command };
export class UpdateMapRunCommand extends $Command
    .classBuilder()
    .ep(commonParams)
    .m(function (Command, cs, config, o) {
    return [
        getSerdePlugin(config, this.serialize, this.deserialize),
        getEndpointPlugin(config, Command.getEndpointParameterInstructions()),
    ];
})
    .s("AWSStepFunctions", "UpdateMapRun", {})
    .n("SFNClient", "UpdateMapRunCommand")
    .f(void 0, void 0)
    .ser(se_UpdateMapRunCommand)
    .de(de_UpdateMapRunCommand)
    .build() {
}
