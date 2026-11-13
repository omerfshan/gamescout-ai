<?php
declare(strict_types=1);
namespace Tests\Feature;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;
final class ScoutApiTest extends TestCase
{
    use RefreshDatabase;
    private function createUser(string $email): User
    {
        return User::create([
            'name' => 'Scout Araştırmacı',
            'email' => $email,
            'password' => 'demo-scout-2026',
        ]);
    }
    public function test_unauthenticated_scout_requests_are_rejected(): void
    {
        $this->getJson('/api/v1/scout/latest')->assertUnauthorized();
        $this->postJson('/api/v1/scout/runs', ['provider' => 'heuristic'])->assertUnauthorized();
    }
    public function test_run_market_scout_and_fetch_latest_isolated_by_user(): void
    {
        $user1 = $this->createUser('scout1@gamescout.local');
        $user2 = $this->createUser('scout2@gamescout.local');
        $token1 = $user1->createToken('test')->plainTextToken;
        $token2 = $user2->createToken('test')->plainTextToken;
        $this->withToken($token1)
            ->getJson('/api/v1/scout/latest')
            ->assertOk()
            ->assertJsonPath('data', null);
        $runResponse = $this->withToken($token1)
            ->postJson('/api/v1/scout/runs', ['provider' => 'heuristic'])
            ->assertCreated();
        $scanId = (string) $runResponse->json('data.scan_id');
        $this->assertNotSame('', $scanId);
        $this->assertCount(3, (array) $runResponse->json('data.actionable_game_proposals'));
        $this->assertGreaterThanOrEqual(3, count((array) $runResponse->json('data.top_genre_insights')));
        $this->assertNotSame('', (string) $runResponse->json('data.ai_engine_used'));
        $this->withToken($token1)
            ->getJson('/api/v1/scout/latest')
            ->assertOk()
            ->assertJsonPath('data.scan_id', $scanId)
            ->assertJsonCount(3, 'data.actionable_game_proposals');
        $this->withToken($token2)
            ->getJson('/api/v1/scout/latest')
            ->assertOk()
            ->assertJsonPath('data', null);
    }
}
