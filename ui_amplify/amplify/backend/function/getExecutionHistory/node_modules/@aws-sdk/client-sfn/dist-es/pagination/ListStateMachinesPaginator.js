import { createPaginator } from "@smithy/core";
import { ListStateMachinesCommand, } from "../commands/ListStateMachinesCommand";
import { SFNClient } from "../SFNClient";
export const paginateListStateMachines = createPaginator(SFNClient, ListStateMachinesCommand, "nextToken", "nextToken", "maxResults");
