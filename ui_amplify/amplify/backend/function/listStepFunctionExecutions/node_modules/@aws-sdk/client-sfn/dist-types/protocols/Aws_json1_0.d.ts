import { HttpRequest as __HttpRequest, HttpResponse as __HttpResponse } from "@smithy/protocol-http";
import { SerdeContext as __SerdeContext } from "@smithy/types";
import { CreateActivityCommandInput, CreateActivityCommandOutput } from "../commands/CreateActivityCommand";
import { CreateStateMachineAliasCommandInput, CreateStateMachineAliasCommandOutput } from "../commands/CreateStateMachineAliasCommand";
import { CreateStateMachineCommandInput, CreateStateMachineCommandOutput } from "../commands/CreateStateMachineCommand";
import { DeleteActivityCommandInput, DeleteActivityCommandOutput } from "../commands/DeleteActivityCommand";
import { DeleteStateMachineAliasCommandInput, DeleteStateMachineAliasCommandOutput } from "../commands/DeleteStateMachineAliasCommand";
import { DeleteStateMachineCommandInput, DeleteStateMachineCommandOutput } from "../commands/DeleteStateMachineCommand";
import { DeleteStateMachineVersionCommandInput, DeleteStateMachineVersionCommandOutput } from "../commands/DeleteStateMachineVersionCommand";
import { DescribeActivityCommandInput, DescribeActivityCommandOutput } from "../commands/DescribeActivityCommand";
import { DescribeExecutionCommandInput, DescribeExecutionCommandOutput } from "../commands/DescribeExecutionCommand";
import { DescribeMapRunCommandInput, DescribeMapRunCommandOutput } from "../commands/DescribeMapRunCommand";
import { DescribeStateMachineAliasCommandInput, DescribeStateMachineAliasCommandOutput } from "../commands/DescribeStateMachineAliasCommand";
import { DescribeStateMachineCommandInput, DescribeStateMachineCommandOutput } from "../commands/DescribeStateMachineCommand";
import { DescribeStateMachineForExecutionCommandInput, DescribeStateMachineForExecutionCommandOutput } from "../commands/DescribeStateMachineForExecutionCommand";
import { GetActivityTaskCommandInput, GetActivityTaskCommandOutput } from "../commands/GetActivityTaskCommand";
import { GetExecutionHistoryCommandInput, GetExecutionHistoryCommandOutput } from "../commands/GetExecutionHistoryCommand";
import { ListActivitiesCommandInput, ListActivitiesCommandOutput } from "../commands/ListActivitiesCommand";
import { ListExecutionsCommandInput, ListExecutionsCommandOutput } from "../commands/ListExecutionsCommand";
import { ListMapRunsCommandInput, ListMapRunsCommandOutput } from "../commands/ListMapRunsCommand";
import { ListStateMachineAliasesCommandInput, ListStateMachineAliasesCommandOutput } from "../commands/ListStateMachineAliasesCommand";
import { ListStateMachinesCommandInput, ListStateMachinesCommandOutput } from "../commands/ListStateMachinesCommand";
import { ListStateMachineVersionsCommandInput, ListStateMachineVersionsCommandOutput } from "../commands/ListStateMachineVersionsCommand";
import { ListTagsForResourceCommandInput, ListTagsForResourceCommandOutput } from "../commands/ListTagsForResourceCommand";
import { PublishStateMachineVersionCommandInput, PublishStateMachineVersionCommandOutput } from "../commands/PublishStateMachineVersionCommand";
import { RedriveExecutionCommandInput, RedriveExecutionCommandOutput } from "../commands/RedriveExecutionCommand";
import { SendTaskFailureCommandInput, SendTaskFailureCommandOutput } from "../commands/SendTaskFailureCommand";
import { SendTaskHeartbeatCommandInput, SendTaskHeartbeatCommandOutput } from "../commands/SendTaskHeartbeatCommand";
import { SendTaskSuccessCommandInput, SendTaskSuccessCommandOutput } from "../commands/SendTaskSuccessCommand";
import { StartExecutionCommandInput, StartExecutionCommandOutput } from "../commands/StartExecutionCommand";
import { StartSyncExecutionCommandInput, StartSyncExecutionCommandOutput } from "../commands/StartSyncExecutionCommand";
import { StopExecutionCommandInput, StopExecutionCommandOutput } from "../commands/StopExecutionCommand";
import { TagResourceCommandInput, TagResourceCommandOutput } from "../commands/TagResourceCommand";
import { TestStateCommandInput, TestStateCommandOutput } from "../commands/TestStateCommand";
import { UntagResourceCommandInput, UntagResourceCommandOutput } from "../commands/UntagResourceCommand";
import { UpdateMapRunCommandInput, UpdateMapRunCommandOutput } from "../commands/UpdateMapRunCommand";
import { UpdateStateMachineAliasCommandInput, UpdateStateMachineAliasCommandOutput } from "../commands/UpdateStateMachineAliasCommand";
import { UpdateStateMachineCommandInput, UpdateStateMachineCommandOutput } from "../commands/UpdateStateMachineCommand";
import { ValidateStateMachineDefinitionCommandInput, ValidateStateMachineDefinitionCommandOutput } from "../commands/ValidateStateMachineDefinitionCommand";
/**
 * serializeAws_json1_0CreateActivityCommand
 */
export declare const se_CreateActivityCommand: (input: CreateActivityCommandInput, context: __SerdeContext) => Promise<__HttpRequest>;
/**
 * serializeAws_json1_0CreateStateMachineCommand
 */
export declare const se_CreateStateMachineCommand: (input: CreateStateMachineCommandInput, context: __SerdeContext) => Promise<__HttpRequest>;
/**
 * serializeAws_json1_0CreateStateMachineAliasCommand
 */
export declare const se_CreateStateMachineAliasCommand: (input: CreateStateMachineAliasCommandInput, context: __SerdeContext) => Promise<__HttpRequest>;
/**
 * serializeAws_json1_0DeleteActivityCommand
 */
export declare const se_DeleteActivityCommand: (input: DeleteActivityCommandInput, context: __SerdeContext) => Promise<__HttpRequest>;
/**
 * serializeAws_json1_0DeleteStateMachineCommand
 */
export declare const se_DeleteStateMachineCommand: (input: DeleteStateMachineCommandInput, context: __SerdeContext) => Promise<__HttpRequest>;
/**
 * serializeAws_json1_0DeleteStateMachineAliasCommand
 */
export declare const se_DeleteStateMachineAliasCommand: (input: DeleteStateMachineAliasCommandInput, context: __SerdeContext) => Promise<__HttpRequest>;
/**
 * serializeAws_json1_0DeleteStateMachineVersionCommand
 */
export declare const se_DeleteStateMachineVersionCommand: (input: DeleteStateMachineVersionCommandInput, context: __SerdeContext) => Promise<__HttpRequest>;
/**
 * serializeAws_json1_0DescribeActivityCommand
 */
export declare const se_DescribeActivityCommand: (input: DescribeActivityCommandInput, context: __SerdeContext) => Promise<__HttpRequest>;
/**
 * serializeAws_json1_0DescribeExecutionCommand
 */
export declare const se_DescribeExecutionCommand: (input: DescribeExecutionCommandInput, context: __SerdeContext) => Promise<__HttpRequest>;
/**
 * serializeAws_json1_0DescribeMapRunCommand
 */
export declare const se_DescribeMapRunCommand: (input: DescribeMapRunCommandInput, context: __SerdeContext) => Promise<__HttpRequest>;
/**
 * serializeAws_json1_0DescribeStateMachineCommand
 */
export declare const se_DescribeStateMachineCommand: (input: DescribeStateMachineCommandInput, context: __SerdeContext) => Promise<__HttpRequest>;
/**
 * serializeAws_json1_0DescribeStateMachineAliasCommand
 */
export declare const se_DescribeStateMachineAliasCommand: (input: DescribeStateMachineAliasCommandInput, context: __SerdeContext) => Promise<__HttpRequest>;
/**
 * serializeAws_json1_0DescribeStateMachineForExecutionCommand
 */
export declare const se_DescribeStateMachineForExecutionCommand: (input: DescribeStateMachineForExecutionCommandInput, context: __SerdeContext) => Promise<__HttpRequest>;
/**
 * serializeAws_json1_0GetActivityTaskCommand
 */
export declare const se_GetActivityTaskCommand: (input: GetActivityTaskCommandInput, context: __SerdeContext) => Promise<__HttpRequest>;
/**
 * serializeAws_json1_0GetExecutionHistoryCommand
 */
export declare const se_GetExecutionHistoryCommand: (input: GetExecutionHistoryCommandInput, context: __SerdeContext) => Promise<__HttpRequest>;
/**
 * serializeAws_json1_0ListActivitiesCommand
 */
export declare const se_ListActivitiesCommand: (input: ListActivitiesCommandInput, context: __SerdeContext) => Promise<__HttpRequest>;
/**
 * serializeAws_json1_0ListExecutionsCommand
 */
export declare const se_ListExecutionsCommand: (input: ListExecutionsCommandInput, context: __SerdeContext) => Promise<__HttpRequest>;
/**
 * serializeAws_json1_0ListMapRunsCommand
 */
export declare const se_ListMapRunsCommand: (input: ListMapRunsCommandInput, context: __SerdeContext) => Promise<__HttpRequest>;
/**
 * serializeAws_json1_0ListStateMachineAliasesCommand
 */
export declare const se_ListStateMachineAliasesCommand: (input: ListStateMachineAliasesCommandInput, context: __SerdeContext) => Promise<__HttpRequest>;
/**
 * serializeAws_json1_0ListStateMachinesCommand
 */
export declare const se_ListStateMachinesCommand: (input: ListStateMachinesCommandInput, context: __SerdeContext) => Promise<__HttpRequest>;
/**
 * serializeAws_json1_0ListStateMachineVersionsCommand
 */
export declare const se_ListStateMachineVersionsCommand: (input: ListStateMachineVersionsCommandInput, context: __SerdeContext) => Promise<__HttpRequest>;
/**
 * serializeAws_json1_0ListTagsForResourceCommand
 */
export declare const se_ListTagsForResourceCommand: (input: ListTagsForResourceCommandInput, context: __SerdeContext) => Promise<__HttpRequest>;
/**
 * serializeAws_json1_0PublishStateMachineVersionCommand
 */
export declare const se_PublishStateMachineVersionCommand: (input: PublishStateMachineVersionCommandInput, context: __SerdeContext) => Promise<__HttpRequest>;
/**
 * serializeAws_json1_0RedriveExecutionCommand
 */
export declare const se_RedriveExecutionCommand: (input: RedriveExecutionCommandInput, context: __SerdeContext) => Promise<__HttpRequest>;
/**
 * serializeAws_json1_0SendTaskFailureCommand
 */
export declare const se_SendTaskFailureCommand: (input: SendTaskFailureCommandInput, context: __SerdeContext) => Promise<__HttpRequest>;
/**
 * serializeAws_json1_0SendTaskHeartbeatCommand
 */
export declare const se_SendTaskHeartbeatCommand: (input: SendTaskHeartbeatCommandInput, context: __SerdeContext) => Promise<__HttpRequest>;
/**
 * serializeAws_json1_0SendTaskSuccessCommand
 */
export declare const se_SendTaskSuccessCommand: (input: SendTaskSuccessCommandInput, context: __SerdeContext) => Promise<__HttpRequest>;
/**
 * serializeAws_json1_0StartExecutionCommand
 */
export declare const se_StartExecutionCommand: (input: StartExecutionCommandInput, context: __SerdeContext) => Promise<__HttpRequest>;
/**
 * serializeAws_json1_0StartSyncExecutionCommand
 */
export declare const se_StartSyncExecutionCommand: (input: StartSyncExecutionCommandInput, context: __SerdeContext) => Promise<__HttpRequest>;
/**
 * serializeAws_json1_0StopExecutionCommand
 */
export declare const se_StopExecutionCommand: (input: StopExecutionCommandInput, context: __SerdeContext) => Promise<__HttpRequest>;
/**
 * serializeAws_json1_0TagResourceCommand
 */
export declare const se_TagResourceCommand: (input: TagResourceCommandInput, context: __SerdeContext) => Promise<__HttpRequest>;
/**
 * serializeAws_json1_0TestStateCommand
 */
export declare const se_TestStateCommand: (input: TestStateCommandInput, context: __SerdeContext) => Promise<__HttpRequest>;
/**
 * serializeAws_json1_0UntagResourceCommand
 */
export declare const se_UntagResourceCommand: (input: UntagResourceCommandInput, context: __SerdeContext) => Promise<__HttpRequest>;
/**
 * serializeAws_json1_0UpdateMapRunCommand
 */
export declare const se_UpdateMapRunCommand: (input: UpdateMapRunCommandInput, context: __SerdeContext) => Promise<__HttpRequest>;
/**
 * serializeAws_json1_0UpdateStateMachineCommand
 */
export declare const se_UpdateStateMachineCommand: (input: UpdateStateMachineCommandInput, context: __SerdeContext) => Promise<__HttpRequest>;
/**
 * serializeAws_json1_0UpdateStateMachineAliasCommand
 */
export declare const se_UpdateStateMachineAliasCommand: (input: UpdateStateMachineAliasCommandInput, context: __SerdeContext) => Promise<__HttpRequest>;
/**
 * serializeAws_json1_0ValidateStateMachineDefinitionCommand
 */
export declare const se_ValidateStateMachineDefinitionCommand: (input: ValidateStateMachineDefinitionCommandInput, context: __SerdeContext) => Promise<__HttpRequest>;
/**
 * deserializeAws_json1_0CreateActivityCommand
 */
export declare const de_CreateActivityCommand: (output: __HttpResponse, context: __SerdeContext) => Promise<CreateActivityCommandOutput>;
/**
 * deserializeAws_json1_0CreateStateMachineCommand
 */
export declare const de_CreateStateMachineCommand: (output: __HttpResponse, context: __SerdeContext) => Promise<CreateStateMachineCommandOutput>;
/**
 * deserializeAws_json1_0CreateStateMachineAliasCommand
 */
export declare const de_CreateStateMachineAliasCommand: (output: __HttpResponse, context: __SerdeContext) => Promise<CreateStateMachineAliasCommandOutput>;
/**
 * deserializeAws_json1_0DeleteActivityCommand
 */
export declare const de_DeleteActivityCommand: (output: __HttpResponse, context: __SerdeContext) => Promise<DeleteActivityCommandOutput>;
/**
 * deserializeAws_json1_0DeleteStateMachineCommand
 */
export declare const de_DeleteStateMachineCommand: (output: __HttpResponse, context: __SerdeContext) => Promise<DeleteStateMachineCommandOutput>;
/**
 * deserializeAws_json1_0DeleteStateMachineAliasCommand
 */
export declare const de_DeleteStateMachineAliasCommand: (output: __HttpResponse, context: __SerdeContext) => Promise<DeleteStateMachineAliasCommandOutput>;
/**
 * deserializeAws_json1_0DeleteStateMachineVersionCommand
 */
export declare const de_DeleteStateMachineVersionCommand: (output: __HttpResponse, context: __SerdeContext) => Promise<DeleteStateMachineVersionCommandOutput>;
/**
 * deserializeAws_json1_0DescribeActivityCommand
 */
export declare const de_DescribeActivityCommand: (output: __HttpResponse, context: __SerdeContext) => Promise<DescribeActivityCommandOutput>;
/**
 * deserializeAws_json1_0DescribeExecutionCommand
 */
export declare const de_DescribeExecutionCommand: (output: __HttpResponse, context: __SerdeContext) => Promise<DescribeExecutionCommandOutput>;
/**
 * deserializeAws_json1_0DescribeMapRunCommand
 */
export declare const de_DescribeMapRunCommand: (output: __HttpResponse, context: __SerdeContext) => Promise<DescribeMapRunCommandOutput>;
/**
 * deserializeAws_json1_0DescribeStateMachineCommand
 */
export declare const de_DescribeStateMachineCommand: (output: __HttpResponse, context: __SerdeContext) => Promise<DescribeStateMachineCommandOutput>;
/**
 * deserializeAws_json1_0DescribeStateMachineAliasCommand
 */
export declare const de_DescribeStateMachineAliasCommand: (output: __HttpResponse, context: __SerdeContext) => Promise<DescribeStateMachineAliasCommandOutput>;
/**
 * deserializeAws_json1_0DescribeStateMachineForExecutionCommand
 */
export declare const de_DescribeStateMachineForExecutionCommand: (output: __HttpResponse, context: __SerdeContext) => Promise<DescribeStateMachineForExecutionCommandOutput>;
/**
 * deserializeAws_json1_0GetActivityTaskCommand
 */
export declare const de_GetActivityTaskCommand: (output: __HttpResponse, context: __SerdeContext) => Promise<GetActivityTaskCommandOutput>;
/**
 * deserializeAws_json1_0GetExecutionHistoryCommand
 */
export declare const de_GetExecutionHistoryCommand: (output: __HttpResponse, context: __SerdeContext) => Promise<GetExecutionHistoryCommandOutput>;
/**
 * deserializeAws_json1_0ListActivitiesCommand
 */
export declare const de_ListActivitiesCommand: (output: __HttpResponse, context: __SerdeContext) => Promise<ListActivitiesCommandOutput>;
/**
 * deserializeAws_json1_0ListExecutionsCommand
 */
export declare const de_ListExecutionsCommand: (output: __HttpResponse, context: __SerdeContext) => Promise<ListExecutionsCommandOutput>;
/**
 * deserializeAws_json1_0ListMapRunsCommand
 */
export declare const de_ListMapRunsCommand: (output: __HttpResponse, context: __SerdeContext) => Promise<ListMapRunsCommandOutput>;
/**
 * deserializeAws_json1_0ListStateMachineAliasesCommand
 */
export declare const de_ListStateMachineAliasesCommand: (output: __HttpResponse, context: __SerdeContext) => Promise<ListStateMachineAliasesCommandOutput>;
/**
 * deserializeAws_json1_0ListStateMachinesCommand
 */
export declare const de_ListStateMachinesCommand: (output: __HttpResponse, context: __SerdeContext) => Promise<ListStateMachinesCommandOutput>;
/**
 * deserializeAws_json1_0ListStateMachineVersionsCommand
 */
export declare const de_ListStateMachineVersionsCommand: (output: __HttpResponse, context: __SerdeContext) => Promise<ListStateMachineVersionsCommandOutput>;
/**
 * deserializeAws_json1_0ListTagsForResourceCommand
 */
export declare const de_ListTagsForResourceCommand: (output: __HttpResponse, context: __SerdeContext) => Promise<ListTagsForResourceCommandOutput>;
/**
 * deserializeAws_json1_0PublishStateMachineVersionCommand
 */
export declare const de_PublishStateMachineVersionCommand: (output: __HttpResponse, context: __SerdeContext) => Promise<PublishStateMachineVersionCommandOutput>;
/**
 * deserializeAws_json1_0RedriveExecutionCommand
 */
export declare const de_RedriveExecutionCommand: (output: __HttpResponse, context: __SerdeContext) => Promise<RedriveExecutionCommandOutput>;
/**
 * deserializeAws_json1_0SendTaskFailureCommand
 */
export declare const de_SendTaskFailureCommand: (output: __HttpResponse, context: __SerdeContext) => Promise<SendTaskFailureCommandOutput>;
/**
 * deserializeAws_json1_0SendTaskHeartbeatCommand
 */
export declare const de_SendTaskHeartbeatCommand: (output: __HttpResponse, context: __SerdeContext) => Promise<SendTaskHeartbeatCommandOutput>;
/**
 * deserializeAws_json1_0SendTaskSuccessCommand
 */
export declare const de_SendTaskSuccessCommand: (output: __HttpResponse, context: __SerdeContext) => Promise<SendTaskSuccessCommandOutput>;
/**
 * deserializeAws_json1_0StartExecutionCommand
 */
export declare const de_StartExecutionCommand: (output: __HttpResponse, context: __SerdeContext) => Promise<StartExecutionCommandOutput>;
/**
 * deserializeAws_json1_0StartSyncExecutionCommand
 */
export declare const de_StartSyncExecutionCommand: (output: __HttpResponse, context: __SerdeContext) => Promise<StartSyncExecutionCommandOutput>;
/**
 * deserializeAws_json1_0StopExecutionCommand
 */
export declare const de_StopExecutionCommand: (output: __HttpResponse, context: __SerdeContext) => Promise<StopExecutionCommandOutput>;
/**
 * deserializeAws_json1_0TagResourceCommand
 */
export declare const de_TagResourceCommand: (output: __HttpResponse, context: __SerdeContext) => Promise<TagResourceCommandOutput>;
/**
 * deserializeAws_json1_0TestStateCommand
 */
export declare const de_TestStateCommand: (output: __HttpResponse, context: __SerdeContext) => Promise<TestStateCommandOutput>;
/**
 * deserializeAws_json1_0UntagResourceCommand
 */
export declare const de_UntagResourceCommand: (output: __HttpResponse, context: __SerdeContext) => Promise<UntagResourceCommandOutput>;
/**
 * deserializeAws_json1_0UpdateMapRunCommand
 */
export declare const de_UpdateMapRunCommand: (output: __HttpResponse, context: __SerdeContext) => Promise<UpdateMapRunCommandOutput>;
/**
 * deserializeAws_json1_0UpdateStateMachineCommand
 */
export declare const de_UpdateStateMachineCommand: (output: __HttpResponse, context: __SerdeContext) => Promise<UpdateStateMachineCommandOutput>;
/**
 * deserializeAws_json1_0UpdateStateMachineAliasCommand
 */
export declare const de_UpdateStateMachineAliasCommand: (output: __HttpResponse, context: __SerdeContext) => Promise<UpdateStateMachineAliasCommandOutput>;
/**
 * deserializeAws_json1_0ValidateStateMachineDefinitionCommand
 */
export declare const de_ValidateStateMachineDefinitionCommand: (output: __HttpResponse, context: __SerdeContext) => Promise<ValidateStateMachineDefinitionCommandOutput>;
