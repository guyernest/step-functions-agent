import { Paginator } from "@smithy/types";
import { ListActivitiesCommandInput, ListActivitiesCommandOutput } from "../commands/ListActivitiesCommand";
import { SFNPaginationConfiguration } from "./Interfaces";
/**
 * @public
 */
export declare const paginateListActivities: (config: SFNPaginationConfiguration, input: ListActivitiesCommandInput, ...rest: any[]) => Paginator<ListActivitiesCommandOutput>;
