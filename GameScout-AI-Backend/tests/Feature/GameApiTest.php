<?php
declare(strict_types=1);
namespace Tests\Feature;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;
final class GameApiTest extends TestCase
{
    use RefreshDatabase;
    private function user(string $email): User { return User::create(['name'=>'Demo','email'=>$email,'password'=>'test-password']); }
    private function actingAsToken(User $user): void { $this->withToken($user->createToken('test')->plainTextToken); }
    private function payload(): array { return ['schema_version'=>'1.0.0','data_origin'=>'synthetic_demo','games'=>[['game_id'=>'demo-1','platform'=>'android','external_app_id'=>'demo.app','title'=>'Demo game','developer_profile'=>'unknown','source_record_id'=>'demo-source','normalized_genres'=>['puzzle']]]]; }
    public function test_unauthenticated_request_is_denied(): void { $this->getJson('/api/v1/games')->assertUnauthorized()->assertJsonPath('error.code','unauthenticated'); }
    public function test_other_user_cannot_list_imported_games(): void {
        $this->actingAsToken($this->user('a@example.invalid'));
        $this->postJson('/api/v1/imports',$this->payload())->assertCreated()->assertJsonPath('data.inserted',1);
        $this->postJson('/api/v1/imports',$this->payload())->assertCreated()->assertJsonPath('data.inserted',0);
        $this->actingAsToken($this->user('b@example.invalid'));
        $this->getJson('/api/v1/games')->assertOk()->assertJsonCount(0,'data');
    }
    public function test_invalid_origin_is_rejected(): void {
        $this->actingAsToken($this->user('c@example.invalid'));
        $payload=$this->payload(); $payload['data_origin']='licensed_import';
        $this->postJson('/api/v1/imports',$payload)->assertUnprocessable()->assertJsonPath('error.code','validation_failed');
    }
    public function test_conflicting_repeat_is_rejected(): void {
        $this->actingAsToken($this->user('d@example.invalid'));
        $this->postJson('/api/v1/imports',$this->payload())->assertCreated();
        $payload=$this->payload(); $payload['games'][0]['title']='Conflict';
        $this->postJson('/api/v1/imports',$payload)->assertConflict()->assertJsonPath('error.code','import_conflict');
    }
    public function test_conflict_rolls_back_other_new_records(): void {
        $this->actingAsToken($this->user('e@example.invalid'));
        $this->postJson('/api/v1/imports',$this->payload())->assertCreated();
        $payload=$this->payload();
        $new=$payload['games'][0]; $new['external_app_id']='new.demo'; $new['game_id']='demo-2';
        $payload['games'][0]['title']='Conflict';
        array_unshift($payload['games'],$new);
        $this->postJson('/api/v1/imports',$payload)->assertConflict();
        $this->getJson('/api/v1/games')->assertOk()->assertJsonCount(1,'data');
    }
}
