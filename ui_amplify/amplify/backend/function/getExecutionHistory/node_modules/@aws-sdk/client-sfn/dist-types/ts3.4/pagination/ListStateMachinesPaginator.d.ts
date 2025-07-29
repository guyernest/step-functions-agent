import { Paginator } from "@smithy/types";
import {
  ListStateMachinesCommandInput,
  ListStateMachinesCommandOutput,
} from "../commands/ListStateMachinesCommand";
import { SFNPaginationConfiguration } from "./Interfaces";
export declare const paginateListStateMachines: (
  config: SFNPaginationConfiguration,
  input: ListStateMachinesCommandInput,
  ...rest: any[]
) => Paginator<ListStateMachinesCommandOutput>;
