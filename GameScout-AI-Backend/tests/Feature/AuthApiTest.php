<?php
declare(strict_types=1);
namespace Tests\Feature;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;
final class AuthApiTest extends TestCase
{
    use RefreshDatabase;
    private function createUser(string $email = 'demo@gamescout.local', string $password = 'demo-scout-2026'): User
    {
        return User::create([
            'name' => 'Demo Araştırmacı',
            'email' => $email,
            'password' => $password,
        ]);
    }
    private function demoImportPayload(): array
    {
        return [
            'schema_version' => '1.0.0',
            'data_origin' => 'synthetic_demo',
            'games' => [[
                'game_id' => 'demo-slice-1',
                'platform' => 'android',
                'external_app_id' => 'demo.slice.app',
                'title' => 'Demo Slice Game',
                'developer_profile' => 'indie',
                'source_record_id' => 'demo-slice-source',
                'normalized_genres' => ['puzzle', 'strategy'],
            ]],
        ];
    }
    public function test_login_issues_bearer_token_and_returns_user(): void
    {
        $this->seed(\Database\Seeders\DatabaseSeeder::class);
        $user = User::query()->where('email', 'demo@gamescout.local')->firstOrFail();
        $this->postJson('/api/v1/auth/login', [
            'email' => 'DEMO@gamescout.local',
            'password' => 'demo-scout-2026',
            'device_name' => 'dashboard',
        ])
            ->assertOk()
            ->assertJsonPath('data.user.id', $user->id)
            ->assertJsonPath('data.user.email', 'demo@gamescout.local')
            ->assertJsonPath('data.token_type', 'Bearer')
            ->assertJsonStructure(['data' => ['user' => ['id', 'name', 'email'], 'token', 'token_type']]);
    }
    public function test_login_rejects_wrong_password(): void
    {
        $this->createUser();
        $this->postJson('/api/v1/auth/login', [
            'email' => 'demo@gamescout.local',
            'password' => 'wrong-password-123',
        ])
            ->assertUnauthorized()
            ->assertJsonPath('error.code', 'invalid_credentials');
    }
    public function test_login_rejects_unknown_email(): void
    {
        $this->postJson('/api/v1/auth/login', [
            'email' => 'unknown@gamescout.local',
            'password' => 'demo-scout-2026',
        ])
            ->assertUnauthorized()
            ->assertJsonPath('error.code', 'invalid_credentials');
    }
    public function test_login_validates_payload(): void
    {
        $this->postJson('/api/v1/auth/login', [
            'email' => 'not-an-email',
            'password' => 'short',
        ])
            ->assertUnprocessable()
            ->assertJsonPath('error.code', 'validation_failed');
    }
    public function test_me_and_logout_with_bearer_token(): void
    {
        $user = $this->createUser();
        $loginResponse = $this->postJson('/api/v1/auth/login', [
            'email' => $user->email,
            'password' => 'demo-scout-2026',
        ])->assertOk();
        $token = (string) $loginResponse->json('data.token');
        $this->withToken($token)
            ->getJson('/api/v1/auth/me')
            ->assertOk()
            ->assertJsonPath('data.email', $user->email);
        $this->withToken($token)
            ->postJson('/api/v1/auth/logout')
            ->assertOk()
            ->assertJsonPath('data.logged_out', true);
        $this->assertDatabaseCount('personal_access_tokens', 0);
        $this->withToken($token)
            ->getJson('/api/v1/auth/me')
            ->assertUnauthorized()
            ->assertJsonPath('error.code', 'unauthenticated');
    }
    public function test_end_to_end_login_import_and_isolated_game_list(): void
    {
        $this->createUser('user1@gamescout.local', 'demo-scout-2026');
        $this->createUser('user2@gamescout.local', 'demo-scout-2026');
        $token1 = (string) $this->postJson('/api/v1/auth/login', [
            'email' => 'user1@gamescout.local',
            'password' => 'demo-scout-2026',
        ])->assertOk()->json('data.token');
        $token2 = (string) $this->postJson('/api/v1/auth/login', [
            'email' => 'user2@gamescout.local',
            'password' => 'demo-scout-2026',
        ])->assertOk()->json('data.token');
        $this->withToken($token1)
            ->postJson('/api/v1/imports', $this->demoImportPayload())
            ->assertCreated()
            ->assertJsonPath('data.inserted', 1);
        $this->withToken($token1)
            ->getJson('/api/v1/games')
            ->assertOk()
            ->assertJsonCount(1, 'data')
            ->assertJsonPath('data.0.title', 'Demo Slice Game');
        $this->withToken($token2)
            ->getJson('/api/v1/games')
            ->assertOk()
            ->assertJsonCount(0, 'data');
    }
}
