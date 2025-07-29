import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import { ListExecutionsInput, ListExecutionsOutput } from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SFNClientResolvedConfig,
} from "../SFNClient";
export { __MetadataBearer };
export { $Command };
export interface ListExecutionsCommandInput extends ListExecutionsInput {}
export interface ListExecutionsCommandOutput
  extends ListExecutionsOutput,
    __MetadataBearer {}
declare const ListExecutionsCommand_base: {
  new (
    input: ListExecutionsCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    ListExecutionsCommandInput,
    ListExecutionsCommandOutput,
    SFNClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    ...[input]: [] | [ListExecutionsCommandInput]
  ): import("@smithy/smithy-client").CommandImpl<
    ListExecutionsCommandInput,
    ListExecutionsCommandOutput,
    SFNClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class ListExecutionsCommand extends ListExecutionsCommand_base {
  protected static __types: {
    api: {
      input: ListExecutionsInput;
      output: ListExecutionsOutput;
    };
    sdk: {
      input: ListExecutionsCommandInput;
      output: ListExecutionsCommandOutput;
    };
  };
}
