<?php
declare(strict_types=1);
namespace App\Application\Games;
use App\Domain\Games\{GameCatalog,GameData,ImportConflict};
final readonly class ImportDemoGames
{
    public function __construct(private GameCatalog $catalog) {}
    public function execute(int $ownerId, array $rows): array
    {
        $unique=[];
        foreach ($rows as $row) {
            $game=GameData::fromArray($row);
            $key=$game->platform.'|'.$game->externalAppId;
            if (isset($unique[$key]) && $unique[$key]->toArray()!==$game->toArray()) {
                throw new ImportConflict('Aynı uygulama kimliği için çelişkili kayıt var.');
            }
            $unique[$key]=$game;
        }
        $inserted=$this->catalog->import($ownerId,array_values($unique));
        return ['received'=>count($rows),'unique'=>count($unique),'inserted'=>$inserted,'data_origin'=>'synthetic_demo'];
    }
}
