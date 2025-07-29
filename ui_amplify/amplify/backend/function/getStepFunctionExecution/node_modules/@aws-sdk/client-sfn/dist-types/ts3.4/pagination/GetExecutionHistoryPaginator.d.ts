import { Paginator } from "@smithy/types";
import {
  GetExecutionHistoryCommandInput,
  GetExecutionHistoryCommandOutput,
} from "../commands/GetExecutionHistoryCommand";
import { SFNPaginationConfiguration } from "./Interfaces";
export declare const paginateGetExecutionHistory: (
  config: SFNPaginationConfiguration,
  input: GetExecutionHistoryCommandInput,
  ...rest: any[]
) => Paginator<GetExecutionHistoryCommandOutput>;
