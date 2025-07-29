import { createPaginator } from "@smithy/core";
import { ListExecutionsCommand, } from "../commands/ListExecutionsCommand";
import { SFNClient } from "../SFNClient";
export const paginateListExecutions = createPaginator(SFNClient, ListExecutionsCommand, "nextToken", "nextToken", "maxResults");
