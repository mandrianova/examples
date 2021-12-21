import React, {useCallback, useMemo, useState} from "react";
import {useTranslation} from "react-i18next";
import Button from "../../ui/button";
import {AvatarAction, ChoiceUserInputAction, SystemAction, UserInputAction} from "../../schema";
import WithTooltip from "../../ui/tooltip";
import {AddCircleOutlineIcon, AddIcon, CloseCircleOutlineIcon, HelpCircleIcon} from "../../ui/icons";
import Timeline from "./Timeline";
import classes from "./LessonActionsAddRow.module.css";

type AnyAction = AvatarAction | SystemAction | UserInputAction | ChoiceUserInputAction;

type props = {
  className?: string,
  onAdd?: (type: AnyAction["__typename"]) => void,
  showHelpIcon?: boolean
}


function LessonActionsAdd({onAdd, extras}: {
  onAdd?: props["onAdd"]
  extras?: React.ReactNode
}) {
  const {t} = useTranslation();

  const handlers = useMemo(() => {
    if (!onAdd) {
      return {};
    }

    return {
      "AvatarAction": () => onAdd("AvatarAction"),
      "SystemAction": () => onAdd("SystemAction"),
      "UserInputAction": () => onAdd("UserInputAction"),
      "ChoiceUserInputAction": () => onAdd("ChoiceUserInputAction"),
    }
  }, [onAdd]);

  return (
    <div className={classes.row}>
      <Button className={classes.btn} onClick={handlers.AvatarAction}>
        <AddIcon className={classes.btnIcon}/>
        {t("components.LessonActionsAddRow.AvatarAction")}
      </Button>
      <Button className={classes.btn} onClick={handlers.UserInputAction}>
        <AddIcon className={classes.btnIcon}/>
        {t("components.LessonActionsAddRow.UserInputAction")}
      </Button>
      <Button className={classes.btn} onClick={handlers.SystemAction}>
        <AddIcon className={classes.btnIcon}/>
        {t("components.LessonActionsAddRow.SystemAction")}
      </Button>

      <Button className={classes.btn} onClick={handlers.ChoiceUserInputAction}>
        <AddIcon className={classes.btnIcon}/>
        {t("components.LessonActionsAddRow.ChoiceUserInputAction")}
      </Button>

      <div className={classes.extras}>
        {extras}
      </div>
    </div>
  )
}


export default function LessonActionsAddRow({className, onAdd, showHelpIcon}: props) {
  const {t} = useTranslation();

  return (
    <Timeline.Row className={className}>
      <LessonActionsAdd
        onAdd={onAdd}
        extras={showHelpIcon && (
          <WithTooltip className={classes.extraIcon} helpText={t("components.LessonActionsAddRow.helpText")}>
            <HelpCircleIcon fontSize={16}/>
          </WithTooltip>
        )}
      />
    </Timeline.Row>
  )
}

LessonActionsAddRow.Collapsable = function LessonActionsAddRowCollapsable({onAdd}: props) {
  const [collapsed, setCollapsed] = useState(true)

  const show = useCallback(() => setCollapsed(false), []);
  const hide = useCallback(() => setCollapsed(true), []);

  return (
    <Timeline.Row narrow={collapsed} className={classes.collapsable} onMouseLeave={hide}>
      {collapsed ? (
        <div tabIndex={0} className={classes.placeholder} onClick={show}>
          <div className={classes.separator}/>
          <span className={classes.collapseText}><AddCircleOutlineIcon/></span>
          <div className={classes.separator}/>
        </div>
      ) : (
        <LessonActionsAdd
          onAdd={onAdd}
          extras={(
            <div tabIndex={0} className={classes.extraIcon} onClick={hide}><CloseCircleOutlineIcon/></div>
          )}
        />
      )
      }
    </Timeline.Row>
  )
}
