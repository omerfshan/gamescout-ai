<?php
declare(strict_types=1);
namespace App\Infrastructure\Scout;
use App\Domain\Scout\ScoutReportStore;
use Illuminate\Support\Facades\DB;
final class DbScoutReportStore implements ScoutReportStore
{
    public function save(int $ownerId, array $reportPayload): array
    {
        $now = now();
        DB::table('scout_reports')->insert([
            'user_id' => $ownerId,
            'scan_id' => (string) ($reportPayload['scan_id'] ?? 'scan-unknown'),
            'ai_engine_used' => (string) ($reportPayload['ai_engine_used'] ?? 'deterministic_heuristic'),
            'report_payload' => json_encode($reportPayload, JSON_THROW_ON_ERROR | JSON_UNESCAPED_UNICODE),
            'scanned_at' => $now,
            'created_at' => $now,
            'updated_at' => $now,
        ]);
        return $reportPayload;
    }
    public function latest(int $ownerId): ?array
    {
        $row = DB::table('scout_reports')
            ->where('user_id', $ownerId)
            ->orderByDesc('id')
            ->first();
        if ($row === null) {
            return null;
        }
        /** @var array<string, mixed> $decoded */
        $decoded = json_decode((string) $row->report_payload, true, 512, JSON_THROW_ON_ERROR);
        return $decoded;
    }
}
