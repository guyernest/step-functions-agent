import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { getSerdePlugin } from "@smithy/middleware-serde";
import { Command as $Command } from "@smithy/smithy-client";
import { commonParams } from "../endpoint/EndpointParameters";
import { de_SendTaskHeartbeatCommand, se_SendTaskHeartbeatCommand } from "../protocols/Aws_json1_0";
export { $Command };
export class SendTaskHeartbeatCommand extends $Command
    .classBuilder()
    .ep(commonParams)
    .m(function (Command, cs, config, o) {
    return [
        getSerdePlugin(config, this.serialize, this.deserialize),
        getEndpointPlugin(config, Command.getEndpointParameterInstructions()),
    ];
})
    .s("AWSStepFunctions", "SendTaskHeartbeat", {})
    .n("SFNClient", "SendTaskHeartbeatCommand")
    .f(void 0, void 0)
    .ser(se_SendTaskHeartbeatCommand)
    .de(de_SendTaskHeartbeatCommand)
    .build() {
}
