import { Paginator } from "@smithy/types";
import { ListExecutionsCommandInput, ListExecutionsCommandOutput } from "../commands/ListExecutionsCommand";
import { SFNPaginationConfiguration } from "./Interfaces";
/**
 * @public
 */
export declare const paginateListExecutions: (config: SFNPaginationConfiguration, input: ListExecutionsCommandInput, ...rest: any[]) => Paginator<ListExecutionsCommandOutput>;
