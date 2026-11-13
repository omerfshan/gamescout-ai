<?php

declare(strict_types=1);

namespace Tests\Feature;

use App\Domain\Scout\MarketScoutRunner;
use App\Infrastructure\Scout\PythonCliMarketScoutRunner;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

final class ScoutApiTest extends TestCase
{
    use RefreshDatabase;

    private function token(string $email = 'researcher@example.test'): string
    {
        return User::create(['name' => 'Researcher', 'email' => $email, 'password' => 'test-password'])
            ->createToken('test')->plainTextToken;
    }

    private function report(): array
    {
        $evidence = [
            'evidence_id' => 'ev_demo_1', 'source' => 'reddit', 'source_label' => 'Synthetic request',
            'subject' => 'Mobile game request', 'quote' => 'I want a short offline puzzle game.',
            'original_text' => 'I want a short offline puzzle game.', 'rating' => null,
            'url' => null, 'fetched_at' => null, 'published_at' => null, 'signal_kind' => 'request',
            'data_origin' => 'synthetic_demo', 'language' => 'en', 'translation_text' => null,
        ];
        return [
            'scan_id' => 'scout-test-1', 'scanned_at' => '2026-11-14T00:00:00Z',
            'ai_engine_used' => 'fake_model', 'ai_engine_label' => 'Deterministic model fixture',
            'status' => 'completed', 'data_origin' => 'synthetic_demo',
            'sources_summary' => ['app_store_count' => 0, 'google_play_count' => 0, 'reddit_count' => 1,
                'total_signals' => 1, 'live_sources_used' => []],
            'model_metadata' => ['model' => 'fake', 'prompt_version' => 'test-v1', 'call_count' => 2, 'review_required' => true],
            'evidence_snapshot' => [$evidence],
            'player_needs' => [['need_id' => 'need-1', 'statement' => 'Short offline puzzle sessions',
                'evidence_ids' => ['ev_demo_1'], 'counter_evidence_ids' => [], 'limitations' => ['One synthetic request.']]],
            'top_genre_insights' => [],
            'actionable_game_proposals' => [[
                'opportunity_id' => 'idea-1', 'recommended_genre' => 'puzzle',
                'concept_title' => 'A hypothetical pocket puzzle', 'tagline' => 'Brief sessions',
                'why_people_want_this' => 'The sample requests short offline puzzles.',
                'core_loop' => 'Arrange tiles, solve, unlock the next puzzle.', 'target_audience' => 'Commuters',
                'solved_complaints' => ['No connection needed'], 'monetization_model' => 'Hypothesis: one-time purchase',
                'risks' => ['Limited evidence'], 'prototype_plan' => 'Test a five-puzzle prototype with users.',
                'story_and_world' => '', 'characters_and_npcs' => '', 'player_actions' => '',
                'unique_mechanics' => [], 'early_experience' => null, 'retention_hooks' => [],
                'progression_and_rewards' => '', 'similar_games_and_differences' => '', 'platform_fit' => '',
                'small_team_feasibility' => '', 'ai_verdict' => '', 'evidence_quotes' => [$evidence],
                'evidence_ids' => ['ev_demo_1'], 'need_ids' => ['need-1'], 'counter_evidence_ids' => [],
                'hypothesis_label' => 'unvalidated_design_hypothesis',
            ]],
            'warnings' => ['Synthetic evaluation fixture, not market evidence.'],
        ];
    }

    private function fakeRunner(array $report): MarketScoutRunner
    {
        $runner = new class($report) implements MarketScoutRunner {
            public array $calls = [];
            public function __construct(private array $report) {}
            public function run(string $provider = 'ollama', string $genre = 'all'): array
            {
                $this->calls[] = [$provider, $genre];
                return $this->report;
            }
        };
        $this->app->instance(MarketScoutRunner::class, $runner);
        return $runner;
    }

    public function test_unauthenticated_requests_are_rejected(): void
    {
        $this->getJson('/api/v1/scout/latest')->assertUnauthorized();
        $this->postJson('/api/v1/scout/runs', [])->assertUnauthorized();
    }

    public function test_valid_model_report_is_saved_and_isolated_by_owner(): void
    {
        $runner = $this->fakeRunner($this->report());
        $token1 = $this->token();
        $token2 = $this->token('other@example.test');
        $this->withToken($token1)->postJson('/api/v1/scout/runs', ['provider' => 'auto', 'genre' => 'puzzle'])
            ->assertCreated()->assertJsonPath('data.status', 'completed');
        $this->assertSame([['ollama', 'puzzle']], $runner->calls);
        $this->withToken($token1)->getJson('/api/v1/scout/latest')
            ->assertOk()->assertJsonPath('data.scan_id', 'scout-test-1');
        $this->withToken($token2)->getJson('/api/v1/scout/latest')->assertOk()->assertJsonPath('data', null);
    }

    public function test_corrupted_nested_report_is_not_saved(): void
    {
        $report = $this->report();
        $report['actionable_game_proposals'] = [[]];
        $this->fakeRunner($report);
        $this->withToken($this->token())->postJson('/api/v1/scout/runs')->assertStatus(500);
        $this->assertDatabaseCount('scout_reports', 0);
    }

    public function test_unknown_citation_and_fabricated_quote_are_rejected(): void
    {
        foreach (['unknown_id', 'changed_quote'] as $case) {
            $report = $this->report();
            if ($case === 'unknown_id') {
                $report['player_needs'][0]['evidence_ids'] = ['ev_not_collected'];
            } else {
                $report['actionable_game_proposals'][0]['evidence_quotes'][0]['quote'] = 'A fabricated complaint.';
            }
            $this->fakeRunner($report);
            $this->withToken($this->token($case.'@example.test'))->postJson('/api/v1/scout/runs')->assertStatus(500);
            $this->assertDatabaseCount('scout_reports', 0);
        }
    }

    public function test_missing_model_is_explicit_without_invented_ideas(): void
    {
        $report = $this->report();
        $report['status'] = 'model_unavailable';
        $report['actionable_game_proposals'] = [];
        $report['player_needs'] = [];
        $report['model_metadata']['call_count'] = 0;
        $this->fakeRunner($report);
        $this->withToken($this->token())->postJson('/api/v1/scout/runs')
            ->assertCreated()->assertJsonPath('data.status', 'model_unavailable')
            ->assertJsonCount(0, 'data.actionable_game_proposals');
    }

    public function test_live_apple_evidence_cannot_be_relabelled_as_reddit(): void
    {
        $report = $this->report();
        $report['data_origin'] = 'live';
        $report['evidence_snapshot'][0]['data_origin'] = 'live';
        $report['evidence_snapshot'][0]['url'] = 'https://itunes.apple.com/us/rss/customerreviews/id=123/json';
        $report['evidence_snapshot'][0]['fetched_at'] = '2026-11-14T00:00:00Z';
        $report['actionable_game_proposals'][0]['evidence_quotes'] = $report['evidence_snapshot'];
        $this->fakeRunner($report);
        $this->withToken($this->token())->postJson('/api/v1/scout/runs')->assertStatus(500);
        $this->assertDatabaseCount('scout_reports', 0);
    }

    public function test_paid_providers_and_invalid_genre_are_rejected_without_server_opt_in(): void
    {
        config(['scout.allowed_providers' => ['ollama']]);
        $token = $this->token();
        foreach (['openai', 'gemini'] as $provider) {
            $this->withToken($token)->postJson('/api/v1/scout/runs', ['provider' => $provider])
                ->assertUnprocessable()->assertJsonPath('error.code', 'validation_failed');
        }
        $this->withToken($token)->postJson('/api/v1/scout/runs', ['genre' => 'invalid_genre'])
            ->assertUnprocessable();
        $this->assertDatabaseCount('scout_reports', 0);
    }

    public function test_metadata_does_not_expose_internal_service_url(): void
    {
        $response = $this->withToken($this->token())->getJson('/api/v1/scout/latest')->assertOk();
        $this->assertArrayNotHasKey('ollama_base_url', $response->json('meta'));
        $response->assertJsonPath('meta.allowed_providers', ['ollama']);
    }

    public function test_real_offline_cli_does_not_invent_ideas_without_model(): void
    {
        config(['scout.allowed_providers' => ['ollama', 'heuristic']]);
        $this->app->bind(MarketScoutRunner::class, PythonCliMarketScoutRunner::class);
        $this->withToken($this->token())->postJson('/api/v1/scout/runs', ['provider' => 'heuristic'])
            ->assertCreated()->assertJsonCount(0, 'data.actionable_game_proposals');
    }
}
