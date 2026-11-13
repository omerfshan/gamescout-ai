<?php
declare(strict_types=1);
namespace App\Application\Games;
use App\Domain\Games\{GameCatalog,GameData};
final readonly class ListGames
{
    public function __construct(private GameCatalog $catalog) {}
    public function execute(int $ownerId, ?string $platform): array
    {
        $games=array_map(fn (GameData $game)=>$game->toArray(),$this->catalog->list($ownerId,$platform));
        return ['data'=>$games,'meta'=>['data_origin'=>'synthetic_demo','demo_label'=>'Sentetik demo','count'=>count($games)]];
    }
}
