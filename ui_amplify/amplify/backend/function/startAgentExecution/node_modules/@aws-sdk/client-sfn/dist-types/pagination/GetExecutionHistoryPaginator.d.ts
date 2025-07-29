import { Paginator } from "@smithy/types";
import { GetExecutionHistoryCommandInput, GetExecutionHistoryCommandOutput } from "../commands/GetExecutionHistoryCommand";
import { SFNPaginationConfiguration } from "./Interfaces";
/**
 * @public
 */
export declare const paginateGetExecutionHistory: (config: SFNPaginationConfiguration, input: GetExecutionHistoryCommandInput, ...rest: any[]) => Paginator<GetExecutionHistoryCommandOutput>;
