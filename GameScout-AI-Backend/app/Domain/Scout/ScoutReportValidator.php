<?php

declare(strict_types=1);

namespace App\Domain\Scout;

/** Structural and citation integrity gate; semantic truth still needs human review. */
final class ScoutReportValidator
{
    public function validate(array $report): void
    {
        foreach (['scan_id', 'scanned_at', 'ai_engine_used', 'ai_engine_label', 'status', 'data_origin'] as $field) {
            $this->text($report[$field] ?? null, $field);
        }
        $status = $report['status'];
        $origin = $report['data_origin'];
        $this->require(in_array($status, ['completed', 'partial', 'insufficient_data', 'model_unavailable'], true), 'status');
        $this->require(in_array($origin, ['live', 'synthetic_demo', 'no_data'], true), 'data_origin');
        $this->require(strtotime($report['scanned_at']) !== false, 'scanned_at');
        $this->strings($report['warnings'] ?? null, 'warnings');
        $this->require(is_array($report['sources_summary'] ?? null), 'sources_summary');
        foreach (['app_store_count', 'google_play_count', 'reddit_count', 'total_signals'] as $field) {
            $this->require(is_int($report['sources_summary'][$field] ?? null) && $report['sources_summary'][$field] >= 0, 'sources_summary.'.$field);
        }
        $this->strings($report['sources_summary']['live_sources_used'] ?? null, 'sources_summary.live_sources_used');
        $metadata = $report['model_metadata'] ?? null;
        $this->require(is_array($metadata), 'model_metadata');
        $this->require(($metadata['review_required'] ?? null) === true, 'model_metadata.review_required');
        $this->require(is_int($metadata['call_count'] ?? null) && $metadata['call_count'] >= 0 && $metadata['call_count'] <= 2, 'model_metadata.call_count');
        $this->require(!isset($metadata['model']) || is_string($metadata['model']), 'model_metadata.model');
        $this->text($metadata['prompt_version'] ?? null, 'model_metadata.prompt_version');

        $snapshot = $this->items($report['evidence_snapshot'] ?? null, 'evidence_snapshot');
        $this->require(count($snapshot) <= 200, 'evidence_snapshot.limit');
        $evidence = [];
        foreach ($snapshot as $item) {
            $this->require(is_array($item), 'evidence_snapshot.item');
            foreach (['evidence_id', 'source', 'source_label', 'subject', 'quote', 'original_text', 'data_origin', 'signal_kind'] as $field) {
                $this->text($item[$field] ?? null, 'evidence.'.$field);
            }
            $id = $item['evidence_id'];
            $this->require(!isset($evidence[$id]), 'evidence.duplicate_id');
            $this->require($item['quote'] === $item['original_text'], 'evidence.original_quote');
            $this->require($item['data_origin'] === $origin, 'evidence.data_origin');
            $this->require(in_array($item['source'], ['app_store', 'google_play', 'reddit', 'community', 'web'], true), 'evidence.source');
            $this->require(in_array($item['signal_kind'], ['review', 'request', 'discussion', 'article'], true), 'evidence.signal_kind');
            if ($origin === 'live') {
                $url = $item['url'] ?? null;
                $this->require(is_string($url) && filter_var($url, FILTER_VALIDATE_URL) !== false && parse_url($url, PHP_URL_SCHEME) === 'https', 'evidence.url');
                $hosts = [
                    'app_store' => ['itunes.apple.com', 'apps.apple.com'],
                    'google_play' => ['play.google.com'],
                    'reddit' => ['reddit.com', 'www.reddit.com', 'old.reddit.com'],
                ];
                if (isset($hosts[$item['source']])) {
                    $this->require(in_array(strtolower((string) parse_url($url, PHP_URL_HOST)), $hosts[$item['source']], true), 'evidence.source_host');
                }
                $this->require(is_string($item['fetched_at'] ?? null) && strtotime($item['fetched_at']) !== false, 'evidence.fetched_at');
            }
            $evidence[$id] = $item;
        }
        $this->require($report['sources_summary']['total_signals'] === count($snapshot), 'sources_summary.total_signals');
        foreach (['app_store', 'google_play', 'reddit'] as $source) {
            $actual = count(array_filter($snapshot, fn (array $item): bool => $item['source'] === $source));
            $this->require($report['sources_summary'][$source.'_count'] === $actual, 'sources_summary.'.$source.'_count');
        }
        if ($origin === 'no_data') {
            $this->require($snapshot === [], 'no_data.evidence');
        }

        $needs = [];
        foreach ($this->items($report['player_needs'] ?? null, 'player_needs') as $need) {
            $this->require(is_array($need), 'player_needs.item');
            $this->text($need['need_id'] ?? null, 'need.need_id');
            $this->text($need['statement'] ?? null, 'need.statement');
            $this->require(!isset($needs[$need['need_id']]), 'need.duplicate_id');
            $this->references($need['evidence_ids'] ?? null, $evidence, 'need.evidence_ids', true);
            $this->references($need['counter_evidence_ids'] ?? null, $evidence, 'need.counter_evidence_ids');
            $this->strings($need['limitations'] ?? null, 'need.limitations');
            $needs[$need['need_id']] = $need;
        }
        foreach ($this->items($report['top_genre_insights'] ?? null, 'top_genre_insights') as $insight) {
            $this->require(is_array($insight), 'insight');
            foreach (['genre', 'demand_badge', 'summary'] as $field) {
                $this->text($insight[$field] ?? null, 'insight.'.$field);
            }
            $this->strings($insight['pain_points'] ?? null, 'insight.pain_points');
            $this->strings($insight['requested_mechanics'] ?? null, 'insight.requested_mechanics');
            $this->require(is_int($insight['signal_count'] ?? null) && $insight['signal_count'] >= 0 && $insight['signal_count'] <= count($snapshot), 'insight.signal_count');
        }
        $proposals = $this->items($report['actionable_game_proposals'] ?? null, 'actionable_game_proposals');
        $this->require(count($proposals) <= 5, 'proposal.limit');
        if ($status === 'completed') {
            $this->require($proposals !== [] && $needs !== [], 'completed.supported_proposals');
        }
        if ($proposals !== []) {
            $this->text($metadata['model'] ?? null, 'model_metadata.model');
        }
        if (in_array($status, ['model_unavailable', 'insufficient_data'], true)) {
            $this->require($proposals === [], 'unavailable.proposals');
        }
        $ids = [];
        foreach ($proposals as $proposal) {
            $this->require(is_array($proposal), 'proposal');
            foreach (['opportunity_id', 'recommended_genre', 'concept_title', 'tagline', 'why_people_want_this', 'core_loop', 'target_audience', 'monetization_model', 'prototype_plan'] as $field) {
                $this->text($proposal[$field] ?? null, 'proposal.'.$field);
            }
            $this->require(!isset($ids[$proposal['opportunity_id']]), 'proposal.duplicate_id');
            $ids[$proposal['opportunity_id']] = true;
            $this->require(($proposal['hypothesis_label'] ?? null) === 'unvalidated_design_hypothesis', 'proposal.hypothesis_label');
            $this->references($proposal['evidence_ids'] ?? null, $evidence, 'proposal.evidence_ids', true);
            $this->references($proposal['need_ids'] ?? null, $needs, 'proposal.need_ids', true);
            $this->references($proposal['counter_evidence_ids'] ?? null, $evidence, 'proposal.counter_evidence_ids');
            $support = [];
            foreach ($proposal['need_ids'] as $id) {
                $support = array_merge($support, $needs[$id]['evidence_ids']);
            }
            $this->require(array_diff($proposal['evidence_ids'], $support) === [], 'proposal.need_support');
            foreach (['solved_complaints', 'risks', 'unique_mechanics', 'retention_hooks'] as $field) {
                $this->strings($proposal[$field] ?? null, 'proposal.'.$field);
            }
            foreach (['story_and_world', 'characters_and_npcs', 'player_actions', 'progression_and_rewards', 'similar_games_and_differences', 'platform_fit', 'small_team_feasibility', 'ai_verdict'] as $field) {
                $this->require(is_string($proposal[$field] ?? null), 'proposal.'.$field);
            }
            $early = $proposal['early_experience'] ?? null;
            if ($early !== null) {
                $this->require(is_array($early), 'proposal.early_experience');
                foreach (['minute_5', 'minute_15', 'minute_30'] as $field) {
                    $this->text($early[$field] ?? null, 'proposal.early_experience.'.$field);
                }
            }
            $quotes = $this->items($proposal['evidence_quotes'] ?? null, 'proposal.evidence_quotes');
            $quoteIds = [];
            foreach ($quotes as $quote) {
                $this->require(is_array($quote) && is_string($quote['evidence_id'] ?? null), 'proposal.evidence_quote');
                $id = $quote['evidence_id'];
                $this->require(isset($evidence[$id]) && in_array($id, $proposal['evidence_ids'], true), 'proposal.evidence_quote_id');
                $this->require(($quote['quote'] ?? null) === $evidence[$id]['original_text'] && ($quote['original_text'] ?? null) === $evidence[$id]['original_text'] && ($quote['source'] ?? null) === $evidence[$id]['source'] && ($quote['url'] ?? null) === ($evidence[$id]['url'] ?? null), 'proposal.evidence_quote_fidelity');
                $quoteIds[] = $id;
            }
            $this->require(count($quoteIds) === count(array_unique($quoteIds)) && array_diff($proposal['evidence_ids'], $quoteIds) === [], 'proposal.evidence_quotes_complete');
        }
    }

    private function require(bool $condition, string $field): void
    {
        if (!$condition) {
            throw new \RuntimeException('Scout raporu doğrulanamadı: '.$field);
        }
    }
    private function text(mixed $value, string $field): void
    {
        $this->require(is_string($value) && trim($value) !== '' && strlen($value) <= 20000, $field);
    }
    private function items(mixed $value, string $field): array
    {
        $this->require(is_array($value) && array_is_list($value), $field);
        return $value;
    }
    private function strings(mixed $value, string $field): void
    {
        foreach ($this->items($value, $field) as $item) {
            $this->text($item, $field);
        }
    }
    private function references(mixed $ids, array $known, string $field, bool $required = false): void
    {
        $this->strings($ids, $field);
        $this->require((!$required || $ids !== []) && count($ids) === count(array_unique($ids)), $field);
        $this->require(array_diff($ids, array_keys($known)) === [], $field);
    }
}
