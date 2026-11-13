<?php
declare(strict_types=1);
namespace App\Http\Requests;
use Illuminate\Foundation\Http\FormRequest;
use Illuminate\Validation\Rule;
final class ImportGamesRequest extends FormRequest
{
    public function authorize(): bool { return $this->user()!==null; }
    public function rules(): array
    {
        return [
            'schema_version'=>['required',Rule::in(['1.0.0'])],
            'data_origin'=>['required',Rule::in(['synthetic_demo'])],
            'games'=>['required','array','list','min:1','max:1000'],
            'games.*'=>['required','array'],
            'games.*.game_id'=>['required','string','max:128'],
            'games.*.platform'=>['required',Rule::in(['android','ios'])],
            'games.*.external_app_id'=>['required','string','max:255'],
            'games.*.title'=>['required','string','max:255'],
            'games.*.developer_profile'=>['required',Rule::in(['indie','small_team','unknown'])],
            'games.*.source_record_id'=>['required','string','max:255'],
            'games.*.normalized_genres'=>['present','array','list','max:30'],
            'games.*.normalized_genres.*'=>['required','string','max:100'],
        ];
    }
}
