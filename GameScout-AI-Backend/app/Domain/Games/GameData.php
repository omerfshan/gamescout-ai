<?php
declare(strict_types=1);
namespace App\Domain\Games;
final readonly class GameData
{
    public function __construct(public string $gameId, public string $platform,
        public string $externalAppId, public string $title, public string $developerProfile,
        public string $sourceRecordId, public array $genres)
    {
        foreach ([$gameId,$externalAppId,$title,$sourceRecordId] as $value) {
            if (trim($value)==='') { throw new \InvalidArgumentException('Boş oyun alanı.'); }
        }
        if (!in_array($platform,['android','ios'],true) || !in_array($developerProfile,['indie','small_team','unknown'],true)) {
            throw new \InvalidArgumentException('Geçersiz platform veya geliştirici profili.');
        }
        foreach ($genres as $genre) {
            if (!is_string($genre) || trim($genre)==='') { throw new \InvalidArgumentException('Geçersiz tür.'); }
        }
    }
    public static function fromArray(array $data): self
    {
        return new self($data['game_id'],$data['platform'],$data['external_app_id'],$data['title'],
            $data['developer_profile'],$data['source_record_id'],$data['normalized_genres']);
    }
    public function toArray(): array
    {
        return ['game_id'=>$this->gameId,'platform'=>$this->platform,'external_app_id'=>$this->externalAppId,
            'title'=>$this->title,'developer_profile'=>$this->developerProfile,
            'source_record_id'=>$this->sourceRecordId,'normalized_genres'=>$this->genres];
    }
}
