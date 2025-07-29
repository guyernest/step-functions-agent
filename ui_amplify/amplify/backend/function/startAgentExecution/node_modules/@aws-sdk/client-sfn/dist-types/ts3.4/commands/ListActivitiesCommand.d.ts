import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import { ListActivitiesInput, ListActivitiesOutput } from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SFNClientResolvedConfig,
} from "../SFNClient";
export { __MetadataBearer };
export { $Command };
export interface ListActivitiesCommandInput extends ListActivitiesInput {}
export interface ListActivitiesCommandOutput
  extends ListActivitiesOutput,
    __MetadataBearer {}
declare const ListActivitiesCommand_base: {
  new (
    input: ListActivitiesCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    ListActivitiesCommandInput,
    ListActivitiesCommandOutput,
    SFNClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    ...[input]: [] | [ListActivitiesCommandInput]
  ): import("@smithy/smithy-client").CommandImpl<
    ListActivitiesCommandInput,
    ListActivitiesCommandOutput,
    SFNClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class ListActivitiesCommand extends ListActivitiesCommand_base {
  protected static __types: {
    api: {
      input: ListActivitiesInput;
      output: ListActivitiesOutput;
    };
    sdk: {
      input: ListActivitiesCommandInput;
      output: ListActivitiesCommandOutput;
    };
  };
}
