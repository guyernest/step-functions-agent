import { createPaginator } from "@smithy/core";
import { ListMapRunsCommand } from "../commands/ListMapRunsCommand";
import { SFNClient } from "../SFNClient";
export const paginateListMapRuns = createPaginator(SFNClient, ListMapRunsCommand, "nextToken", "nextToken", "maxResults");
