<?php

declare(strict_types=1);

namespace App\Http\Requests;

use Illuminate\Foundation\Http\FormRequest;
use Illuminate\Validation\Rule;

final class RunScoutRequest extends FormRequest
{
    public const VALID_GENRES = [
        'all',
        'action',
        'rpg',
        'strategy',
        'roguelike',
        'simulation',
        'puzzle',
        'survival',
        'casual',
        'racing_sports',
        'adventure',
        'tower_defense',
        'cozy_simulation',
        'action_survival',
        'rpg_guild',
    ];

    public function authorize(): bool
    {
        return $this->user() !== null;
    }

    public function rules(): array
    {
        return [
            'provider' => ['sometimes', 'string', Rule::in(array_merge(['auto'], config('scout.allowed_providers', ['ollama'])))],
            'genre' => ['sometimes', 'string', 'nullable', Rule::in(self::VALID_GENRES)],
        ];
    }
}
