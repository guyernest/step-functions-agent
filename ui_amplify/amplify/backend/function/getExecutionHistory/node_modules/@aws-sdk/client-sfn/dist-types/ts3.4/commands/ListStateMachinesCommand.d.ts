import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import {
  ListStateMachinesInput,
  ListStateMachinesOutput,
} from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SFNClientResolvedConfig,
} from "../SFNClient";
export { __MetadataBearer };
export { $Command };
export interface ListStateMachinesCommandInput extends ListStateMachinesInput {}
export interface ListStateMachinesCommandOutput
  extends ListStateMachinesOutput,
    __MetadataBearer {}
declare const ListStateMachinesCommand_base: {
  new (
    input: ListStateMachinesCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    ListStateMachinesCommandInput,
    ListStateMachinesCommandOutput,
    SFNClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    ...[input]: [] | [ListStateMachinesCommandInput]
  ): import("@smithy/smithy-client").CommandImpl<
    ListStateMachinesCommandInput,
    ListStateMachinesCommandOutput,
    SFNClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class ListStateMachinesCommand extends ListStateMachinesCommand_base {
  protected static __types: {
    api: {
      input: ListStateMachinesInput;
      output: ListStateMachinesOutput;
    };
    sdk: {
      input: ListStateMachinesCommandInput;
      output: ListStateMachinesCommandOutput;
    };
  };
}
