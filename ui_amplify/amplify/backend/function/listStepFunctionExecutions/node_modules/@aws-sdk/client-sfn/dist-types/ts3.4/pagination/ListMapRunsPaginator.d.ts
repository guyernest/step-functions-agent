import { Paginator } from "@smithy/types";
import {
  ListMapRunsCommandInput,
  ListMapRunsCommandOutput,
} from "../commands/ListMapRunsCommand";
import { SFNPaginationConfiguration } from "./Interfaces";
export declare const paginateListMapRuns: (
  config: SFNPaginationConfiguration,
  input: ListMapRunsCommandInput,
  ...rest: any[]
) => Paginator<ListMapRunsCommandOutput>;
