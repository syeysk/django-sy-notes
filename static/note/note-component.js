NoteComponent = {
    template: `
        <teleport to="h1">[[ title ]]</teleport>
        <note-viewer-component
            :class="{'d-none': mode == 'edit'}"
            :content_html="!syntaxErrorMessage ? content_html : 'Не удалось отобразить содержимое по причине: ' + syntaxErrorMessage + '.'"
        ></note-viewer-component>
        <note-editor-component
            v-if="is_authenticated && mode != 'view'"
            :title="title"
            :content="content"
            :error-message="errorMessage"
            :success-message="successMessage"
            @save="save"
            @cancel="cancel"
        ></note-editor-component>
        <br>
        <div style="text-align: center;" :class="{'d-none': mode == 'edit'}" v-if="is_authenticated && has_access_to_edit">
            <input type="button" value="Редактировать заметку" @click="edit" class="btn btn-outline-secondary">
        </div>
    `,
    components: {NoteViewerComponent, NoteEditorComponent},
    data() {
        let note_object = JSON.parse(document.getElementById('note_json').textContent);
        is_new = !Boolean(note_object);
        return {
            title: is_new ? '' : note_object.title,
            content: is_new ? '' : note_object.content,
            syntaxErrorMessage: is_new ? '' : note_object.error_message,
            content_html: is_new ? '' : note_object.content_html,
            errorMessage: '',
            successMessage: '',
            mode: is_new ? 'edit' : 'view',
            is_new: is_new,
            has_access_to_edit: HAS_ACCESS_TO_EDIT,
            is_authenticated: IS_AUTHENTICATED,
        }
    },
    methods: {
        edit() {
            this.mode = 'edit';
        },
        view() {
            if (!this.syntaxErrorMessage) {
                this.mode = 'view';
            }
        },
        cancel(event, editor, title, content) {
            editor.mTitle = this.title;
            editor.mContent = this.content;
            this.view();
        },
        save(event, title, content, images, toggle_mode) {
            let url = document.createElement('a');
            url.href = location.href;
            url.pathname += URL_SAVE_NOTE;

            let self = this;
            this.successMessage = 'Сохраняем...';
            let form = event.target.form;
            title = title.trim();
            let form_data = new FormData();
            form_data.append('title', title);
            form_data.append('content', content);
            for (hashed_name of images.keys()) {
                let image = images.get(hashed_name);
                form_data.append('images', image, hashed_name);
            }
            if (this.is_new) {
                $.ajax({
                    url: url.href,
                    headers: {
                        "X-CSRFToken": CSRF_TOKEN,
                    },
                    contentType: false,
                    dataType: false,
                    processData: false,
                    data: form_data,
                    success: function(result) {
                        if (result.error_message) {
                            self.errorMessage = result.error_message;
                            self.successMessage = '';
                            return;
                        }

                        clear_status_fields(form);
                        set_valid_field(form, result.updated_fields);
                        self.successMessage = '';
                        self.badMessage = '';
                        history.pushState(
                            null,
                            null,
                            location.href.replace('/new', '/' + encodeURI(title) + '.md'),
                        );
                        self.title = title;
                        self.content = content;
                        self.syntaxErrorMessage = '';
                        self.content_html = result.content_html;
                        images.clear();
                        if (toggle_mode) {
                            self.view();
                        }
                        self.is_new = false;
                    },
                    statusCode: {
                        500: function(xhr) {
                            self.errorMessage = 'ошибка сохранения'
                        },
                        400: function(xhr) {
                            clear_status_fields(form);
                            set_invalid_field(form, xhr.responseJSON);
                            self.errorMessage = ''
                        },
                        401: function(xhr) {
                            clear_status_fields(form);
                            self.errorMessage = xhr.responseJSON.detail;
                        },
                        403: function(xhr) {
                            clear_status_fields(form);
                            self.errorMessage = xhr.responseJSON.detail;
                        },                            },
                    method: "post",
                });
            } else {
                $.ajax({
                    url: url.href,
                    headers: {
                        "X-CSRFToken": CSRF_TOKEN,
                    },
                    contentType: false,
                    dataType: false,
                    processData: false,
                    data: form_data,
                    success: function(result) {
                        if (result.error_message) {
                            self.errorMessage = 'Мы сохранили заметку, хотя она не отобразится, т. к.: ' + result.error_message;
                            self.successMessage = '';
                            return;
                        }

                        clear_status_fields(form);
                        set_valid_field(form, result.updated_fields);
                        self.successMessage = '';
                        self.badMessage = '';
                        history.pushState(
                            null,
                            null,
                            location.href.replace('/' + encodeURI(self.title), '/' + encodeURI(title)),
                        );
                        self.title = title;
                        self.content = content;
                        self.syntaxErrorMessage = '';
                        self.content_html = result.content_html;
                        images.clear();
                        if (toggle_mode) {
                            self.view();
                        }
                    },
                    statusCode: {
                        500: function(xhr) {
                            self.errorMessage = 'ошибка сохранения'
                        },
                        400: function(xhr) {
                            clear_status_fields(form);
                            set_invalid_field(form, xhr.responseJSON);
                            self.errorMessage = ''
                        },
                        401: function(xhr) {
                            clear_status_fields(form);
                            self.errorMessage = xhr.responseJSON.detail;
                        },
                        403: function(xhr) {
                            clear_status_fields(form);
                            self.errorMessage = xhr.responseJSON.detail;
                        },
                        404: function(xhr) {
                            clear_status_fields(form);
                            self.errorMessage = 'Заметка с таким названием не существует. Возможно, она была переименована'
                        },
                    },
                    method: "put",
                });
            }
        }
    },
}
