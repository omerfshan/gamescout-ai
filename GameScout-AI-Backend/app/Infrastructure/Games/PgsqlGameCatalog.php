<?php
declare(strict_types=1);
namespace App\Infrastructure\Games;
use App\Domain\Games\{GameCatalog,GameData,ImportConflict};
use Illuminate\Support\Facades\DB;
final class PgsqlGameCatalog implements GameCatalog
{
    public function import(int $ownerId, array $games): int
    {
        return DB::transaction(function () use ($ownerId,$games): int {
            // Serialize imports for one owner, including when no game row exists yet.
            DB::table('users')->where('id',$ownerId)->lockForUpdate()->firstOrFail();
            $inserted=0;
            foreach ($games as $game) {
                $key=['user_id'=>$ownerId,'platform'=>$game->platform,'external_app_id'=>$game->externalAppId];
                $existing=DB::table('games')->where($key)->first();
                if ($existing) {
                    if ($this->hydrate($existing)->toArray()!==$game->toArray()) {
                        throw new ImportConflict('Önceki içe aktarımla çelişen kayıt var.');
                    }
                    continue;
                }
                DB::table('games')->insert($key+[
                    'game_id'=>$game->gameId,'title'=>$game->title,'developer_profile'=>$game->developerProfile,
                    'source_record_id'=>$game->sourceRecordId,'normalized_genres'=>json_encode($game->genres,JSON_THROW_ON_ERROR),
                    'data_origin'=>'synthetic_demo','created_at'=>now(),'updated_at'=>now(),
                ]);
                $inserted++;
            }
            return $inserted;
        });
    }
    public function list(int $ownerId, ?string $platform): array
    {
        return DB::table('games')->where('user_id',$ownerId)
            ->when($platform,fn ($query)=>$query->where('platform',$platform))
            ->orderBy('platform')->orderBy('external_app_id')->get()->map(fn ($row)=>$this->hydrate($row))->all();
    }
    private function hydrate(object $row): GameData
    {
        return new GameData($row->game_id,$row->platform,$row->external_app_id,$row->title,
            $row->developer_profile,$row->source_record_id,json_decode($row->normalized_genres,true,512,JSON_THROW_ON_ERROR));
    }
}
