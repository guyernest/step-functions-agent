import { createPaginator } from "@smithy/core";
import { ListActivitiesCommand, } from "../commands/ListActivitiesCommand";
import { SFNClient } from "../SFNClient";
export const paginateListActivities = createPaginator(SFNClient, ListActivitiesCommand, "nextToken", "nextToken", "maxResults");
