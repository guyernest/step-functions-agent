import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { getSerdePlugin } from "@smithy/middleware-serde";
import { Command as $Command } from "@smithy/smithy-client";
import { commonParams } from "../endpoint/EndpointParameters";
import { TestStateInputFilterSensitiveLog, TestStateOutputFilterSensitiveLog, } from "../models/models_0";
import { de_TestStateCommand, se_TestStateCommand } from "../protocols/Aws_json1_0";
export { $Command };
export class TestStateCommand extends $Command
    .classBuilder()
    .ep(commonParams)
    .m(function (Command, cs, config, o) {
    return [
        getSerdePlugin(config, this.serialize, this.deserialize),
        getEndpointPlugin(config, Command.getEndpointParameterInstructions()),
    ];
})
    .s("AWSStepFunctions", "TestState", {})
    .n("SFNClient", "TestStateCommand")
    .f(TestStateInputFilterSensitiveLog, TestStateOutputFilterSensitiveLog)
    .ser(se_TestStateCommand)
    .de(de_TestStateCommand)
    .build() {
}
